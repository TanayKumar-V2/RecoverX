from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from cohere import (
    JsonObjectResponseFormatV2,
    TextAssistantMessageResponseContentItem,
    UserChatMessageV2,
)

from app.ai.cache import LLMCache
from app.ai.cohere_client import create_cohere_client
from app.ai.prompts import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)
from app.ai.schemas import CohereDiagnosisResponse
from app.core.config import get_settings
from app.domain.enums import DiagnosisSource
from app.domain.models import Diagnosis, Payment


class CohereDiagnosisError(RuntimeError):
    """Raised when Cohere cannot produce a valid diagnosis."""


class CohereClassifier:
    def __init__(
        self,
        cache: LLMCache | None = None,
    ) -> None:
        self.settings = get_settings()
        self.client = create_cohere_client()
        self.cache = cache or LLMCache()

    def _cache_key(
        self,
        payment: Payment,
    ) -> str:
        payload = {
            "provider": "cohere",
            "model": self.settings.cohere_model,
            "prompt_version": PROMPT_VERSION,
            "payment": payment.model_dump(mode="json"),
        }

        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def _response_schema() -> JsonObjectResponseFormatV2:
        return JsonObjectResponseFormatV2(
        type="json_object",
        json_schema={
            "type": "object",
            "required": [
                "root_cause",
                "confidence",
                "recommended_action",
                "reasoning",
            ],
            "properties": {
                "root_cause": {
                    "type": "string",
                    "enum": [
                        "insufficient_funds",
                        "expired_card",
                        "hard_decline",
                        "soft_decline",
                        "fraud_flag",
                        "transient_glitch",
                    ],
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
                "recommended_action": {
                    "type": "string",
                    "enum": [
                        "smart_retry",
                        "send_update_link",
                        "immediate_retry",
                        "escalate_manual_review",
                        "stop_no_action",
                    ],
                },
                "reasoning": {
                    "type": "string",
                },
            },
        },
    )

    def classify(
        self,
        payment: Payment,
    ) -> Diagnosis:

        cache_key = self._cache_key(payment)

        cached = self.cache.get(cache_key)

        if cached is not None:
            diagnosis = CohereDiagnosisResponse.model_validate(cached)

            return Diagnosis(
                payment_id=payment.payment_id,
                root_cause=diagnosis.root_cause,
                confidence=diagnosis.confidence,
                source=DiagnosisSource.LLM,
                recommended_action=diagnosis.recommended_action,
                reasoning=diagnosis.reasoning,
                model_name=self.settings.cohere_model,
                prompt_version=PROMPT_VERSION,
                latency_ms=0,
            )

        payment_data = json.dumps(
            payment.model_dump(mode="json"),
            indent=2,
        )

        user_prompt = USER_PROMPT_TEMPLATE.format(payment_data=payment_data)

        start_time = time.perf_counter()

        try:
            response = self.client.chat(
                model=self.settings.cohere_model,
                messages=[
                    UserChatMessageV2(
                        role="user",
                        content=(f"{SYSTEM_PROMPT}\n\n{user_prompt}"),
                    )
                ],
                response_format=self._response_schema(),
                temperature=0,
            )

        except Exception as exc:
            raise CohereDiagnosisError(f"Cohere request failed: {exc}") from exc

        latency_ms = (time.perf_counter() - start_time) * 1000

        content = response.message.content

        if not content:
            raise CohereDiagnosisError("Cohere returned an empty response.")

        first_item = content[0]

        if not isinstance(
            first_item,
            TextAssistantMessageResponseContentItem,
        ):
            raise CohereDiagnosisError("Cohere returned a non-text response.")

        try:
            raw_response = json.loads(first_item.text)
        except json.JSONDecodeError as exc:
            raise CohereDiagnosisError("Cohere returned invalid JSON.") from exc

        try:
            diagnosis = CohereDiagnosisResponse.model_validate(raw_response)
        except Exception as exc:
            raise CohereDiagnosisError(
                "Cohere response failed schema validation."
            ) from exc

        response_payload = diagnosis.model_dump(mode="json")

        self.cache.set(
            cache_key=cache_key,
            provider="cohere",
            model=self.settings.cohere_model,
            prompt_version=PROMPT_VERSION,
            response=response_payload,
        )

        return Diagnosis(
            payment_id=payment.payment_id,
            root_cause=diagnosis.root_cause,
            confidence=diagnosis.confidence,
            source=DiagnosisSource.LLM,
            recommended_action=diagnosis.recommended_action,
            reasoning=diagnosis.reasoning,
            model_name=self.settings.cohere_model,
            prompt_version=PROMPT_VERSION,
            latency_ms=round(latency_ms, 2),
        )
