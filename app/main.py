from cohere import (
    TextAssistantMessageResponseContentItem,
    UserChatMessageV2,
)
from fastapi import FastAPI

from app.ai.cohere_client import create_cohere_client
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="AI-powered subscription revenue recovery engine",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "revloop",
    }


@app.get("/health/cohere")
def cohere_health_check() -> dict[str, str]:
    client = create_cohere_client()

    response = client.chat(
        model=settings.cohere_model,
        messages=[
            UserChatMessageV2(
                content="Reply with exactly: RevLoop Cohere connection OK"
            )
        ],
        temperature=0,
    )

    content = response.message.content

    if not content:
        raise RuntimeError("Cohere returned an empty response.")

    first_item = content[0]

    if not isinstance(first_item, TextAssistantMessageResponseContentItem):
        raise TypeError("Cohere returned a non-text response.")

    return {
        "status": "ok",
        "response": first_item.text,
    }
