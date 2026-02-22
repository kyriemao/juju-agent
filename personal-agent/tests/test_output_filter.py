from agent.output_filter import filter_event


def test_filter_assistant_event() -> None:
    event = {"type": "assistant", "text": "你好"}
    got = filter_event(event, "s1")
    assert got == {"type": "chunk", "content": "你好", "session_id": "s1"}


def test_filter_tool_use_bash_summary() -> None:
    event = {"type": "tool_use", "name": "bash", "input": {"command": "ls -la"}}
    got = filter_event(event, "s1")
    assert got is not None
    assert got["type"] == "tool"
    assert got["tool_name"] == "bash"
    assert "ls -la" in got["content"]


def test_filter_noise_event() -> None:
    assert filter_event({"type": "stats"}, "s1") is None
