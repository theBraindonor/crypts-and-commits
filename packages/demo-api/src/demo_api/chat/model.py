from langchain_openai import ChatOpenAI

from demo_api.chat.config import OPENROUTER_BASE_URL, get_chat_model_name, get_openrouter_api_key


def get_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=get_chat_model_name(),
        api_key=get_openrouter_api_key(),
        base_url=OPENROUTER_BASE_URL,
        streaming=True,
    )
