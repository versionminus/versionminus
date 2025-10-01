from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: Literal["user", "system", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7


@router.post("/completions", summary="Stateless chat completion")
async def chat_completions(req: ChatCompletionRequest):
    # Naive echo/last-message stub; replace with real model invocation.
    user_parts = [m.content for m in req.messages if m.role == "user"]
    answer = "Stub response to: " + (user_parts[-1] if user_parts else "(no user input)")
    return {
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": len(req.messages), "completion_tokens": 5, "total_tokens": len(req.messages) + 5},
    }
