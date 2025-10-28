"""Chunk boundary policy detection via LangChain + LangGraph + local LLM."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from licodex.core.chunking import ChunkBoundaryPolicy, DEFAULT_POLICY
from licodex.core.config import get_settings


try:  # pragma: no cover - optional heavy dependencies
    from langchain_community.llms import LlamaCpp
    from langchain_core.prompts import ChatPromptTemplate
    from langgraph.graph import END, Graph
except Exception:  # pragma: no cover
    LlamaCpp = None  # type: ignore
    ChatPromptTemplate = None  # type: ignore
    Graph = None  # type: ignore
    END = object()  # fallback placeholder


try:  # pragma: no cover - optional MCP dependencies
    from mcp.client import Client
except Exception:  # pragma: no cover
    Client = None  # type: ignore


logger = logging.getLogger("licodex.chunk_policy")


@dataclass
class ChunkPolicyDecision:
    policy: ChunkBoundaryPolicy
    reason: str
    source: str
    tool_used: Optional[str] = None


_GRAPH_CACHE: Optional[Any] = None
_GRAPH_SETTINGS_ID: Optional[str] = None


POLICY_OPTIONS = [p.value for p in ChunkBoundaryPolicy]


def _heuristic_policy(note: str, metadata: Optional[Dict[str, Any]] = None) -> ChunkPolicyDecision:
    lowered = note.lower()
    if "```" in note or "~~~" in note:
        return ChunkPolicyDecision(policy=ChunkBoundaryPolicy.CODE_BLOCKS, reason="Detected fenced code blocks", source="heuristic")
    if any(line.strip().startswith(('#', '##', '###')) for line in note.splitlines() if line.strip()):
        return ChunkPolicyDecision(policy=ChunkBoundaryPolicy.HEADINGS_LISTS, reason="Detected markdown headings", source="heuristic")
    if any(line.strip().startswith(('-', '*', '+', '1.', '2.', '3.')) for line in note.splitlines() if line.strip()):
        return ChunkPolicyDecision(policy=ChunkBoundaryPolicy.HEADINGS_LISTS, reason="Detected list formatting", source="heuristic")
    if len(note.split()) < 120:
        return ChunkPolicyDecision(policy=ChunkBoundaryPolicy.MINIMAL_WORDS, reason="Short note", source="heuristic")
    return ChunkPolicyDecision(policy=DEFAULT_POLICY, reason="Fallback default", source="heuristic")


def _graph_settings_signature() -> str:
    settings = get_settings()
    return "|".join(
        [
            settings.chunk_policy_model_path or "",
            str(settings.chunk_policy_model_ctx),
            str(settings.chunk_policy_model_threads),
        ]
    )


def _get_llm(settings):  # pragma: no cover - heavy path
    if LlamaCpp is None or not settings.chunk_policy_model_path:
        return None
    return LlamaCpp(
        model_path=settings.chunk_policy_model_path,
        n_ctx=settings.chunk_policy_model_ctx,
        n_threads=settings.chunk_policy_model_threads,
        temperature=0.1,
    )


def _build_graph(settings):  # pragma: no cover - heavy path
    if Graph is None or ChatPromptTemplate is None:
        return None

    llm = _get_llm(settings)
    if llm is None:
        return None

    policies_str = ", ".join(POLICY_OPTIONS)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a chunk policy specialist. Choose the best chunk boundary policy for retrieval augmented generation."
                " Policies: {policies}. If you require deterministic heuristics, set use_tool=true and call the tool 'detect_chunk_boundary_policy'."
                " Respond strictly as JSON with keys: policy (string|nullable), reason (string), use_tool (bool), tool_args (object).",
            ),
            (
                "human",
                "Note:\n{note}\n\nMetadata:\n{metadata}\n",
            ),
        ]
    )

    def llm_node(state):
        note = state.get("note", "")
        metadata = state.get("metadata", {})
        trace_id = state.get("trace_id")
        logger.info(
            "chunk_policy.langgraph.llm.invoke",
            extra={
                "trace_id": trace_id,
                "note_chars": len(note or ""),
                "metadata_keys": sorted(metadata.keys()) if isinstance(metadata, dict) else [],
            },
        )
        formatted = prompt.format_prompt(
            note=note,
            metadata=json.dumps(metadata, ensure_ascii=False),
            policies=policies_str,
        )
        raw_response = llm.invoke(formatted.to_string())  # type: ignore[assignment]
        logger.info(
            "chunk_policy.langgraph.llm.result",
            extra={
                "trace_id": trace_id,
                "raw_preview": str(raw_response)[:500],
            },
        )
        try:
            parsed = json.loads(raw_response)
        except Exception:
            parsed = {
                "policy": None,
                "reason": f"Unparsable response: {raw_response[:120]}",
                "use_tool": False,
                "tool_args": {},
            }
        state.update(
            {
                "llm_raw": raw_response,
                "policy": parsed.get("policy"),
                "reason": parsed.get("reason", ""),
                "use_tool": bool(parsed.get("use_tool")),
                "tool_args": parsed.get("tool_args") or {},
            }
        )
        if parsed.get("tool_name"):
            state["tool_name"] = parsed.get("tool_name")
        return state

    async def tool_node(state):
        tool_name = state.get("tool_name") or "detect_chunk_boundary_policy"
        tool_args = state.get("tool_args") or {}
        note = state.get("note", "")
        metadata = state.get("metadata") or {}
        trace_id = state.get("trace_id")
        tool_args.setdefault("note", note)
        tool_args.setdefault("metadata", metadata)
        tool_args.setdefault("trace_id", trace_id)
        logger.info(
            "chunk_policy.langgraph.tool.invoke",
            extra={
                "trace_id": trace_id,
                "tool_name": tool_name,
            },
        )
        result = await _call_mcp_tool(tool_name, tool_args)
        logger.info(
            "chunk_policy.langgraph.tool.result",
            extra={
                "trace_id": trace_id,
                "tool_name": tool_name,
                "result_policy": result.get("policy"),
                "result_reason": result.get("reason"),
            },
        )
        state["policy"] = result.get("policy")
        state["reason"] = result.get("reason", state.get("reason"))
        state["tool_used"] = tool_name
        state["use_tool"] = False
        return state

    def condition(state):
        return "tool" if state.get("use_tool") else "end"

    graph = Graph()
    graph.add_node("llm", llm_node)
    graph.add_node("tool", tool_node)
    graph.set_entry_point("llm")
    graph.add_conditional_edges("llm", condition, {"tool": "tool", "end": END})
    graph.add_edge("tool", END)
    return graph.compile()


async def _call_mcp_tool(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    trace_id = tool_args.get("trace_id")
    logger.info(
        "chunk_policy.mcp.request",
        extra={
            "trace_id": trace_id,
            "tool_name": tool_name,
        },
    )
    if not settings.chunk_policy_mcp_enabled or Client is None:
        decision = _heuristic_policy(tool_args.get("note", ""), tool_args.get("metadata"))
        logger.info(
            "chunk_policy.mcp.disabled",
            extra={
                "trace_id": trace_id,
                "fallback_policy": decision.policy.value,
                "fallback_reason": decision.reason,
            },
        )
        return {
            "policy": decision.policy.value,
            "reason": decision.reason,
            "source": decision.source,
        }

    url = (
        ("wss" if settings.chunk_policy_mcp_use_tls else "ws")
        + f"://{settings.chunk_policy_mcp_host}:{settings.chunk_policy_mcp_port}/ws"
    )
    try:  # pragma: no cover - requires external server
        async with Client(url) as client:  # type: ignore[attr-defined]
            response = await client.call_tool(tool_name, tool_args)  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover
        decision = _heuristic_policy(tool_args.get("note", ""), tool_args.get("metadata"))
        logger.warning(
            "chunk_policy.mcp.error",
            extra={
                "trace_id": trace_id,
                "error": repr(exc),
                "fallback_policy": decision.policy.value,
            },
        )
        return {
            "policy": decision.policy.value,
            "reason": f"MCP fallback: {exc}",
            "source": "mcp-fallback",
        }
    if isinstance(response, dict):
        logger.info(
            "chunk_policy.mcp.response",
            extra={
                "trace_id": trace_id,
                "tool_name": tool_name,
                "response_policy": response.get("policy"),
            },
        )
        return response
    logger.warning(
        "chunk_policy.mcp.unexpected_response",
        extra={
            "trace_id": trace_id,
            "tool_name": tool_name,
            "response_type": type(response).__name__,
        },
    )
    return {
        "policy": None,
        "reason": "Unexpected MCP response",
        "source": "mcp-fallback",
    }


async def detect_chunk_policy(
    note: str,
    override: Optional[ChunkBoundaryPolicy | str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ChunkPolicyDecision:
    """Return the chunk boundary policy for ``note``."""

    start_time = time.perf_counter()
    trace_id = metadata.get("trace_id") if isinstance(metadata, dict) and "trace_id" in metadata else None
    note_hash = hashlib.sha256((note or "").encode("utf-8")).hexdigest()[:12] if note else None
    logger.info(
        "chunk_policy.detect.start",
        extra={
            "trace_id": trace_id,
            "note_hash": note_hash,
            "note_chars": len(note or ""),
            "metadata_keys": sorted(metadata.keys()) if isinstance(metadata, dict) else [],
            "override": str(override) if override else None,
        },
    )

    settings = get_settings()

    if override:
        try:
            policy = ChunkBoundaryPolicy(str(override))
        except ValueError:
            policy = DEFAULT_POLICY
        decision = ChunkPolicyDecision(policy=policy, reason="Request override", source="request")
        logger.info(
            "chunk_policy.detect.finish",
            extra={
                "trace_id": trace_id,
                "policy": decision.policy.value,
                "reason": decision.reason,
                "source": decision.source,
                "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
            },
        )
        return decision

    if not settings.chunk_policy_detection_enabled:
        try:
            policy = ChunkBoundaryPolicy(settings.chunk_boundary_policy_default)
        except ValueError:
            policy = DEFAULT_POLICY
        decision = ChunkPolicyDecision(policy=policy, reason="Detection disabled", source="settings")
        logger.info(
            "chunk_policy.detect.finish",
            extra={
                "trace_id": trace_id,
                "policy": decision.policy.value,
                "reason": decision.reason,
                "source": decision.source,
                "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
            },
        )
        return decision

    global _GRAPH_CACHE, _GRAPH_SETTINGS_ID
    signature = _graph_settings_signature()
    if _GRAPH_CACHE is None or signature != _GRAPH_SETTINGS_ID:
        _GRAPH_CACHE = _build_graph(settings)
        _GRAPH_SETTINGS_ID = signature

    if _GRAPH_CACHE is None:
        # Fallback to heuristics when we cannot build the graph/LLM
        decision = _heuristic_policy(note, metadata)
        logger.info(
            "chunk_policy.detect.finish",
            extra={
                "trace_id": trace_id,
                "policy": decision.policy.value,
                "reason": decision.reason,
                "source": decision.source,
                "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
            },
        )
        return decision

    state = {"note": note, "metadata": metadata or {}, "trace_id": trace_id}
    try:  # pragma: no cover - heavy path with async graph
        if hasattr(_GRAPH_CACHE, "ainvoke"):
            result = await _GRAPH_CACHE.ainvoke(state)
        else:
            # Some langgraph versions expose invoke only; wrap in thread loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _GRAPH_CACHE.invoke, state)
    except Exception as exc:
        decision = _heuristic_policy(note, metadata)
        decision.reason = f"Graph error: {exc}"
        logger.warning(
            "chunk_policy.detect.graph_error",
            extra={
                "trace_id": trace_id,
                "error": repr(exc),
                "fallback_policy": decision.policy.value,
            },
        )
        logger.info(
            "chunk_policy.detect.finish",
            extra={
                "trace_id": trace_id,
                "policy": decision.policy.value,
                "reason": decision.reason,
                "source": decision.source,
                "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
            },
        )
        return decision

    policy_raw = result.get("policy") if isinstance(result, dict) else None
    try:
        policy = ChunkBoundaryPolicy(str(policy_raw)) if policy_raw else DEFAULT_POLICY
    except ValueError:
        policy = DEFAULT_POLICY

    reason = result.get("reason", "LangGraph decision") if isinstance(result, dict) else "LangGraph decision"
    source = "tool" if isinstance(result, dict) and result.get("tool_used") else "detector"
    tool_used = result.get("tool_used") if isinstance(result, dict) else None

    decision = ChunkPolicyDecision(policy=policy, reason=reason, source=source, tool_used=tool_used)
    logger.info(
        "chunk_policy.detect.finish",
        extra={
            "trace_id": trace_id,
            "policy": decision.policy.value,
            "reason": decision.reason,
            "source": decision.source,
            "tool_used": decision.tool_used,
            "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
        },
    )

    return decision


__all__ = [
    "ChunkPolicyDecision",
    "detect_chunk_policy",
]
