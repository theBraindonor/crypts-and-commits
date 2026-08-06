from demo_api.chat.graph import SYSTEM_PROMPT, _build_prompt


def test_prompt_orders_persona_then_priming_then_messages() -> None:
    prompt = _build_prompt("MARKER-PRIMING-TEXT")

    messages = prompt.format_messages(messages=[])

    assert [message.content for message in messages] == [SYSTEM_PROMPT, "MARKER-PRIMING-TEXT"]
