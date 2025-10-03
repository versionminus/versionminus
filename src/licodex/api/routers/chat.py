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
from licodex.core.config import get_settings

from licodex.core.modelhub import get_modelhub_client, resolve_chat_model

router = APIRouter(prefix="/chat", tags=["chat"])


from licodex.schemas.chat import ChatCompletionRequest, ChatThreadMessageResponse, ChatThreadMessageRequest


@router.post("/completions", summary="Stateless chat completion")
async def chat_completions(req: ChatCompletionRequest):
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
        # Fall back to stub behavior on any external error
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
    """Stateful chat entrypoint.

    Steps:
      1. Ensure thread exists (404 if not).
      2. Load existing messages for history (currently entire thread).
      3. Create a new Message row with user content (response empty initially).
      4. Generate stub assistant reply referencing last user message.
      5. Update the same row's response field and commit.
      6. Return structured response with basic usage metrics.

    NOTE: History trimming & real model generation are future concerns.
    """
    # 1. Validate thread
    try:
        await get_thread_or_404(session, payload.thread_id)
    except ThreadNotFoundError:
        raise HTTPException(status_code=404, detail="Thread not found")

    # 2. Retrieve history (single thread) -> list[(Thread, [Message...])]
    rows = await list_messages_per_thread(session, thread_id=payload.thread_id)
    if not rows:
        # Race condition: thread deleted after validation
        raise HTTPException(status_code=404, detail="Thread not found")
    _thread_obj, prior_messages = rows[0]

    # Build a naive textual context (placeholder for real prompt assembly)
    # Each Message currently encodes a user input (content) and possibly a response.
    history_user_texts = [m.content for m in prior_messages if m.content]

    # 3. Create new message with empty response for now
    try:
        msg = await create_message_service(
            session,
            thread_id=payload.thread_id,
            content=payload.content,
            response="",  # filled below
        )
    except MsgThreadNotFoundError:
        raise HTTPException(status_code=404, detail="Thread not found")

    # 4. Generate stub assistant reply
    last_user = payload.content or (history_user_texts[-1] if history_user_texts else "")
    settings = get_settings()

    assistant_reply: str
    # Schema normalized / validated model already
    resolved_model, reason = resolve_chat_model(payload.model)
    if settings.modelhub_api_key and settings.modelhub_base_url:
        # Attempt real call including history (simple concatenation of prior messages)
        try:
            client = get_modelhub_client()
            if client is None:
                raise RuntimeError("modelhub client unavailable")
            # Assemble chat history: treat each stored message.content as user and response as assistant if present
            assembled: list[dict[str, str]] = []
            for pm in prior_messages:
                if pm.content:
                    assembled.append({"role": "user", "content": pm.content})
                if pm.response:
                    assembled.append({"role": "assistant", "content": pm.response})
            # Add current user turn
            assembled.append({"role": "user", "content": payload.content})
            completion = client.chat.completions.create(
                messages=assembled,
                model=resolved_model,
                temperature=payload.temperature,
            )
            assistant_reply = completion.choices[0].message.content  # type: ignore[attr-defined]
        except Exception as e:  # pragma: no cover - network or external failure
            assistant_reply = f"Stub reply (provider error: {e.__class__.__name__}) to: {last_user}".strip()
    else:
        assistant_reply = f"Stub reply (model={resolved_model}) to: {last_user}".strip()

    # 5. Update message row's response and commit
    msg.response = assistant_reply  # type: ignore
    await session.flush()
    await session.commit()

    # 6. Return response. Usage is placeholder; counts total messages now.
    total_messages = len(prior_messages) + 1
    usage = {
        "prompt_messages": total_messages,  # coarse metric
        "completion_messages": 1,
        "total_messages": total_messages + 1,
    }
    return ChatThreadMessageResponse(
        thread_id=payload.thread_id,
        message_id=msg.id,  # type: ignore
        content=payload.content,
        response=assistant_reply,
        model=resolved_model,
        usage=usage,
    )
