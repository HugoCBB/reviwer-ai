from langchain_core.language_models import BaseChatModel
from app.core.config import settings


def get_llm(json_mode: bool = False) -> BaseChatModel:
    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
            format="json" if json_mode else "",
        )

    if settings.llm_provider == "deepseek":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com",
            temperature=settings.llm_temperature,
        )

    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        temperature=settings.llm_temperature,
        google_api_key=settings.google_api_key,
    )
