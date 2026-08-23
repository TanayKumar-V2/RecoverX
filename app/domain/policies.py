from app.domain.enums import RecommendedAction, RootCause


MAX_RETRIES: dict[RecommendedAction, int] = {
    RecommendedAction.SMART_RETRY: 3,
    RecommendedAction.IMMEDIATE_RETRY: 2,
    RecommendedAction.SEND_UPDATE_LINK: 1,
}

COOLDOWN_HOURS: dict[RecommendedAction, int] = {
    RecommendedAction.SMART_RETRY: 48,
    RecommendedAction.IMMEDIATE_RETRY: 1,
    RecommendedAction.SEND_UPDATE_LINK: 72,
}