import cohere

from app.core.config import get_settings


def create_cohere_client() -> cohere.ClientV2:
    settings = get_settings()

    return cohere.ClientV2(
        api_key=settings.get_cohere_api_key(),
    )