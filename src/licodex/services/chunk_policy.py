"""Chunk boundary policy detection via LangChain + LangGraph + local LLM."""

from __future__ import annotations

import asyncio
import json
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
        formatted = prompt.format_prompt(
            note=note,
            metadata=json.dumps(metadata, ensure_ascii=False),
            policies=policies_str,
        )
        raw_response = llm.invoke(formatted.to_string())  # type: ignore[assignment]
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
        tool_args.setdefault("note", note)
        tool_args.setdefault("metadata", metadata)
        result = await _call_mcp_tool(tool_name, tool_args)
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
    if not settings.chunk_policy_mcp_enabled or Client is None:
        decision = _heuristic_policy(tool_args.get("note", ""), tool_args.get("metadata"))
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
        return {
            "policy": decision.policy.value,
            "reason": f"MCP fallback: {exc}",
            "source": "mcp-fallback",
        }
    if isinstance(response, dict):
        return response
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

    settings = get_settings()

    if override:
        try:
            policy = ChunkBoundaryPolicy(str(override))
        except ValueError:
            policy = DEFAULT_POLICY
        return ChunkPolicyDecision(policy=policy, reason="Request override", source="request")

    if not settings.chunk_policy_detection_enabled:
        try:
            policy = ChunkBoundaryPolicy(settings.chunk_boundary_policy_default)
        except ValueError:
            policy = DEFAULT_POLICY
        return ChunkPolicyDecision(policy=policy, reason="Detection disabled", source="settings")

    global _GRAPH_CACHE, _GRAPH_SETTINGS_ID
    signature = _graph_settings_signature()
    if _GRAPH_CACHE is None or signature != _GRAPH_SETTINGS_ID:
        _GRAPH_CACHE = _build_graph(settings)
        _GRAPH_SETTINGS_ID = signature

    if _GRAPH_CACHE is None:
        # Fallback to heuristics when we cannot build the graph/LLM
        return _heuristic_policy(note, metadata)

    state = {"note": note, "metadata": metadata or {}}
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
        return decision

    policy_raw = result.get("policy") if isinstance(result, dict) else None
    try:
        policy = ChunkBoundaryPolicy(str(policy_raw)) if policy_raw else DEFAULT_POLICY
    except ValueError:
        policy = DEFAULT_POLICY

    reason = result.get("reason", "LangGraph decision") if isinstance(result, dict) else "LangGraph decision"
    source = "tool" if result.get("tool_used") else "detector"
    tool_used = result.get("tool_used") if isinstance(result, dict) else None

    return ChunkPolicyDecision(policy=policy, reason=reason, source=source, tool_used=tool_used)


__all__ = [
    "ChunkPolicyDecision",
    "detect_chunk_policy",
]
