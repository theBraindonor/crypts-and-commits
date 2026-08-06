from pathlib import Path

from demo_api.chat.graph import SYSTEM_PROMPT, _build_prompt
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


def test_prompt_orders_persona_then_priming_then_messages() -> None:
    prompt = _build_prompt("MARKER-PRIMING-TEXT")

    messages = prompt.format_messages(messages=[])

    assert [message.content for message in messages] == [SYSTEM_PROMPT, "MARKER-PRIMING-TEXT"]


def test_tool_call_round_trip_executes_and_returns_final_reply(tmp_path: Path, fake_graph) -> None:
    tool_call_reply = AIMessage(content="", tool_calls=[{"name": "list_campaigns", "args": {}, "id": "call_1"}])
    graph = fake_graph(tool_call_reply, "Final answer.", root=tmp_path, priming="MARKER-PRIMING-TEXT")

    result = graph.invoke(
        {"messages": [HumanMessage(content="what campaigns exist?")]},
        config={"configurable": {"thread_id": "t1"}},
    )

    messages = result["messages"]
    assert messages[-1].content == "Final answer."
    tool_messages = [message for message in messages if isinstance(message, ToolMessage)]
    assert len(tool_messages) == 1
    assert tool_messages[0].name == "list_campaigns"
