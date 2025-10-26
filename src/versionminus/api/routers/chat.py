"""Chat router.

Future improvements (not yet implemented):
 - Real model invocation & token counting
 - History truncation / sliding window
 - Distinct roles per record instead of (content, response) pair
 - Streaming responses (see streams router)
 - System / tool messages and moderation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from versionminus.api import deps
from versionminus.services.thread import get_thread_or_404, ThreadNotFoundError, list_messages_per_thread
from versionminus.services.message import (
    create_message as create_message_service,
    ThreadNotFoundError as MsgThreadNotFoundError,
)
from versionminus.services.source import retrieve_relevant_notes, create_sources_for_group
from versionminus.schemas.embeddings import SearchRequest
from versionminus.api.routers.embeddings import search_embeddings as embeddings_search
from versionminus.core.config import get_settings

from versionminus.core.modelhub import get_modelhub_client, resolve_chat_model
from versionminus.core.errors import ResponseTooLongError, NoSuchModelError
from sqlalchemy.exc import DBAPIError
import re

router = APIRouter(prefix="/chat", tags=["chat"])


from versionminus.schemas.chat import ChatCompletionRequest, ChatThreadMessageResponse, ChatThreadMessageRequest


@router.post("/completions", summary="Stateless chat completion")
async def chat_completions(req: ChatCompletionRequest):
        """Stateless chat completion (no persistence).

        This endpoint returns a single assistant reply in an OpenAI-compatible
        ``choices`` structure. No database state is read or written; the full
        conversational context must be supplied every call.

        Model resolution policy:
            - ``model`` is optional; if omitted we inject the configured
                ``settings.chat_completion_model``.
            - Supplying a different value raises a 422 (validated in the schema).
            - The response includes a ``resolution.reason`` field describing why the
                model was chosen (e.g. ``configured_default`` vs future policies).

        Response shape (simplified):
            {
                "model": str,
                "choices": [ { "index": 0, "message": {"role": "assistant", "content": str}, "finish_reason": str } ],
                "usage": { ... provider or placeholder metrics ... },
                "resolution": { "reason": str }
            }

        Current limitations / TODO:
            - No streaming (will be handled by a dedicated streaming route).
            - Token usage may be stubbed if provider is unavailable.
            - Only one configured model is allowed right now.
            - No tool / function call roles yet (limited to user/system/assistant).
        """
        try:
                resolved_model, reason = resolve_chat_model(req.model)
        except NoSuchModelError as e:
                raise HTTPException(status_code=404, detail={"error": {"code": "model_not_found", "message": str(e), "model": e.model}})
        user_parts = [m.content for m in req.messages if m.role == "user"]
        last_user = user_parts[-1] if user_parts else "(no user input)"

        try:
                client = get_modelhub_client()
                if client is not None:
                        completion = client.chat.completions.create(
                                messages=[{"role": m.role, "content": m.content} for m in req.messages],
                                model=resolved_model,
                                temperature=req.temperature,
                        )
                        choice = completion.choices[0]
                        answer = choice.message.content  # type: ignore[attr-defined]
                        usage = getattr(completion, "usage", {}) or {}
                        return {
                                "model": resolved_model,
                                "choices": [
                                        {
                                                "index": 0,
                                                "message": {"role": "assistant", "content": answer},
                                                "finish_reason": getattr(choice, "finish_reason", "stop"),
                                        }
                                ],
                                "usage": usage,
                                "resolution": {"reason": reason},
                        }
                else:
                        answer = "Stub response to: " + last_user
        except Exception as e:  # pragma: no cover - network / external failures
                answer = f"Stub response (provider error: {e.__class__.__name__}) to: {last_user}"

        return {
                "model": resolved_model,
                "choices": [
                        {
                                "index": 0,
                                "message": {"role": "assistant", "content": answer},
                                "finish_reason": "stop",
                        }
                ],
                "usage": {"prompt_tokens": len(req.messages), "completion_tokens": 5, "total_tokens": len(req.messages) + 5},
                "resolution": {"reason": reason},
        }


@router.post(
    "/send",
    response_model=ChatThreadMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a user message (by thread) and get assistant response",
)
async def chat_send(
    payload: ChatThreadMessageRequest,
    session: AsyncSession = Depends(deps.get_db),
):
    """Stateful chat entrypoint (persists user + assistant turn).

    Steps:
      1. Ensure thread exists (404 if not).
      2. Load existing messages for history (currently entire thread).
      3. Create a new Message row with user content (response empty initially).
      4. Generate assistant reply (real model call if configured, else stub).
      5. Update the same row's response field and commit.
      6. Return structured response with basic usage metrics.

    Persistence model:
      Each DB "Message" row currently stores a single user prompt and (after
      generation) the assistant response in the same record. A future schema
      might normalize roles into separate rows to better support system / tool
      messages and multi-assistant scenarios.

    Stateless vs Stateful (comparison to ``POST /chat/completions``):
      - This endpoint automatically reconstructs prior context from storage;
        callers only send the *new* user message.
      - Returns concrete identifiers (``thread_id``, ``message_id``) enabling
        later mutation, retrieval, metrics, and audit.
      - Intended for durable conversations, compliance logging, retrieval
        augmentation, or analytics.
      - If you just need a one-off answer without saving, prefer the stateless
        ``/chat/completions`` route.

    Model resolution:
      - Same hybrid policy as stateless route: optional model param validated
        against the configured default; rejection on mismatch.

    Current limitations / TODO:
      - No history truncation / windowing (loads entire thread each call).
      - Usage metrics are coarse (message counts, not tokens).
      - No streaming; reply is returned after full generation.
      - No system / tool message persistence yet.
    """
    # 1. Validate thread
    try:
        await get_thread_or_404(session, payload.thread_id)
    except ThreadNotFoundError:
        raise HTTPException(status_code=404, detail="Thread not found")

    # 2. Retrieve history (single thread) -> list[(Thread, [Message...])]
    rows = await list_messages_per_thread(session, thread_id=payload.thread_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Thread not found")
    _thread_obj, prior_messages = rows[0]

    history_user_texts = [m.content for m in prior_messages if m.content]

    # 3. Retrieval: attempt embeddings semantic search, fallback to stub heuristic
    import uuid as _uuid
    retrieval_group_id = _uuid.uuid4()
    retrieved_pairs: list[tuple[_uuid.UUID, str, float | None]] = []
    try:  # pragma: no cover - external systems
        sreq = SearchRequest(query=payload.content, top_k=6)
        search_resp = await embeddings_search(sreq)
        hits = (search_resp or {}).get("results", []) if isinstance(search_resp, dict) else []  # type: ignore[index]
        seen_note_ids: set[_uuid.UUID] = set()
        from versionminus.repositories import note as note_repo
        for h in hits:
            if not isinstance(h, dict):
                continue
            nid_raw = h.get("note_id")
            if not nid_raw:
                continue
            try:
                nid = _uuid.UUID(str(nid_raw))
            except Exception:
                continue
            if nid in seen_note_ids:
                continue
            note_obj = await note_repo.get_by_id(session, nid)
            if not note_obj or not getattr(note_obj, "content", None):
                continue
            snippet = note_obj.content[:240].strip() or "(empty note)"
            distance = h.get("distance") if isinstance(h.get("distance"), (int, float)) else None
            retrieved_pairs.append((nid, snippet, distance))
            seen_note_ids.add(nid)
            if len(retrieved_pairs) >= 3:  # limit sources attached to message
                break
    except Exception:  # pragma: no cover
        retrieved_pairs = []
    if not retrieved_pairs:
        # Fallback retrieval (returns triples with distance where available)
        retrieved_pairs = await retrieve_relevant_notes(session, user_query=payload.content)

    # 3b. Persist placeholder message (without response yet) including retrieval group id
    try:
        msg = await create_message_service(
            session,
            thread_id=payload.thread_id,
            content=payload.content,
            response="",
            source=retrieval_group_id,
        )
    except MsgThreadNotFoundError:
        raise HTTPException(status_code=404, detail="Thread not found")

    last_user = payload.content or (history_user_texts[-1] if history_user_texts else "")
    settings = get_settings()
    try:
        resolved_model, reason = resolve_chat_model(payload.model)
    except NoSuchModelError as e:
        raise HTTPException(status_code=404, detail={"error": {"code": "model_not_found", "message": str(e), "model": e.model}})
    # Build retrieval context (RAG augmentation) injected as a system message.
    retrieval_context: str | None = None
    if retrieved_pairs:
        # Load system prompt from configured file path (caching contents in module-level singleton)
        _sys_prompt: str | None = None
        from versionminus.core.config import get_settings as _gs
        _p_settings = _gs()
        import os
        prompt_path = _p_settings.retrieval_system_prompt_path
        # Resolve path relative to project root if necessary
        if not os.path.isabs(prompt_path):
            # Attempt to locate relative to current working dir
            candidate = os.path.join(os.getcwd(), prompt_path)
            prompt_path = candidate if os.path.exists(candidate) else prompt_path
        with open(prompt_path, 'r', encoding='utf-8') as fh:  # noqa: PTH123
            _sys_prompt = fh.read().strip()

        lines: list[str] = []
        for idx, (nid, quote, dist) in enumerate(retrieved_pairs, start=1):
            dist_part = f" (dist={dist:.3f})" if isinstance(dist, (int, float)) else ""
            lines.append(f"{idx}. note_id={nid}{dist_part} -> {quote}")
        retrieval_context = (_sys_prompt + "\n\nRelevant notes:\n" + "\n".join(lines))

    if settings.modelhub_api_key and settings.modelhub_base_url:
        try:
            client = get_modelhub_client()
            if client is None:
                raise RuntimeError("modelhub client unavailable")
            assembled: list[dict[str, str]] = []
            for pm in prior_messages:
                if pm.content:
                    assembled.append({"role": "user", "content": pm.content})
                if pm.response:
                    assembled.append({"role": "assistant", "content": pm.response})
            # Inject retrieval context BEFORE current user question so model can ground answer.
            if retrieval_context:
                assembled.append({"role": "system", "content": retrieval_context})
            assembled.append({"role": "user", "content": payload.content})
            completion = client.chat.completions.create(
                messages=assembled,
                model=resolved_model,
                temperature=payload.temperature,
            )
            assistant_reply = completion.choices[0].message.content  # type: ignore[attr-defined]
        except Exception as e:  # pragma: no cover
            assistant_reply = f"Stub reply (provider error: {e.__class__.__name__}) to: {last_user}".strip()
    else:
        assistant_reply = f"Stub reply (model={resolved_model}) to: {last_user}".strip()

    # 5. Persist reply
    try:
        msg.response = assistant_reply  # type: ignore[attr-defined]
    except Exception:  # assignment itself will not fail, DB flush might
        pass
    # Persist sources rows for retrieval
    if retrieved_pairs:
        await create_sources_for_group(session, sources_id=retrieval_group_id, items=retrieved_pairs)
    try:
        await session.flush()
        await session.commit()
    except DBAPIError as db_err:  # pragma: no cover - depends on DB state
        # Detect legacy varchar length failure (asyncpg StringDataRightTruncationError)
        msg_txt = str(db_err.orig) if getattr(db_err, "orig", None) else str(db_err)
        # attempt to extract limit (e.g., 'value too long for type character varying(255)')
        m = re.search(r"character varying\((\d+)\)", msg_txt)
        limit_int = int(m.group(1)) if m else None
        if "value too long" in msg_txt.lower():
            raise HTTPException(
                status_code=422,
                detail=str(ResponseTooLongError(length=len(assistant_reply or ''), limit=limit_int)),
            ) from db_err
        raise

    # 6. Return response (usage metrics are coarse placeholders)
    total_messages = len(prior_messages) + 1
    usage = {
        "prompt_messages": total_messages,
        "completion_messages": 1,
        "total_messages": total_messages + 1,
    }
    return ChatThreadMessageResponse(
        thread_id=payload.thread_id,
        message_id=msg.id,  # type: ignore[attr-defined]
        content=payload.content,
        response=assistant_reply,
        model=resolved_model,
        usage=usage,
        source_id=retrieval_group_id,
        sources=[{"note_id": str(n_id), "quote": quote, "distance": dist} for (n_id, quote, dist) in retrieved_pairs],
    )
