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

from licodex.api import deps
from licodex.services.thread import get_thread_or_404, ThreadNotFoundError, list_messages_per_thread
from licodex.services.message import (
    create_message as create_message_service,
    ThreadNotFoundError as MsgThreadNotFoundError,
)
from licodex.services.source import retrieve_relevant_notes, create_sources_for_group
from licodex.schemas.embeddings import SearchRequest
from licodex.api.routers.embeddings import search_embeddings as embeddings_search
from licodex.core.config import get_settings

from licodex.core.modelhub import get_modelhub_client, resolve_chat_model

router = APIRouter(prefix="/chat", tags=["chat"])


from licodex.schemas.chat import ChatCompletionRequest, ChatThreadMessageResponse, ChatThreadMessageRequest


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
        resolved_model, reason = resolve_chat_model(req.model)
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
        from licodex.repositories import note as note_repo
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
            retrieved_pairs.append((nid, snippet, None))
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
    resolved_model, reason = resolve_chat_model(payload.model)
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
    msg.response = assistant_reply  # type: ignore[attr-defined]
    # Persist sources rows for retrieval
    if retrieved_pairs:
        await create_sources_for_group(session, sources_id=retrieval_group_id, items=retrieved_pairs)
    await session.flush()
    await session.commit()

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
