"""Filter and format Claude Code stream-json events for frontend consumption."""

from __future__ import annotations

from typing import Any

NOISE_TYPES = {"stats", "system", "debug", "trace"}


def _truncate(text: str, limit: int = 80) -> str:
    return text if len(text) <= limit else f"{text[:limit]}..."


def _tool_input_summary(tool_name: str, payload: dict[str, Any]) -> str:
    tool_input = payload.get("input", {}) if isinstance(payload, dict) else {}
    if tool_name == "bash":
        command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
        return _truncate(command)
    if tool_name in {"read_file", "write_file"}:
        path = tool_input.get("path", "") if isinstance(tool_input, dict) else ""
        if tool_name == "write_file":
            content = tool_input.get("content", "") if isinstance(tool_input, dict) else ""
            line_count = len(content.splitlines()) if content else 0
            return f"{path} ({line_count} lines)"
        return path
    return _truncate(str(tool_input))


def filter_event(raw_event: dict[str, Any], session_id: str) -> dict[str, Any] | None:
    event_type = raw_event.get("type")
    if event_type in NOISE_TYPES:
        return None

    if event_type == "assistant":
        text = raw_event.get("text", "")
        if not text:
            return None
        return {"type": "chunk", "content": text, "session_id": session_id}

    if event_type == "tool_use":
        tool_name = raw_event.get("name", "unknown")
        summary = _tool_input_summary(tool_name, raw_event)
        return {
            "type": "tool",
            "content": f"🔧 {tool_name}: {summary}",
            "session_id": session_id,
            "tool_name": tool_name,
            "metadata": {"summary": summary},
        }

    if event_type == "tool_result":
        summary = _truncate(str(raw_event.get("content", "tool_result")), 120)
        return {
            "type": "tool",
            "content": f"🧩 tool_result: {summary}",
            "session_id": session_id,
            "tool_name": "tool_result",
            "metadata": {"collapsed": True},
        }

    if event_type == "error":
        return {
            "type": "error",
            "content": raw_event.get("message", "Unknown error"),
            "session_id": session_id,
        }

    return None
