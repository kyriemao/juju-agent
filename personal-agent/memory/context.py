"""Context injection hooks reserved for future memory integration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class InjectedContext:
    session_id: str
    content: str = ""


def inject_context(session_id: str) -> InjectedContext:
    """Placeholder for future memory injection before Claude execution."""
    return InjectedContext(session_id=session_id)
