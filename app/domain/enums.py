from enum import Enum


class RootCause(str, Enum):
    INSUFFICIENT_FUNDS = "insufficient_funds"
    EXPIRED_CARD = "expired_card"
    HARD_DECLINE = "hard_decline"
    SOFT_DECLINE = "soft_decline"
    FRAUD_FLAG = "fraud_flag"
    TRANSIENT_GLITCH = "transient_glitch"


class RecommendedAction(str, Enum):
    SMART_RETRY = "smart_retry"
    SEND_UPDATE_LINK = "send_update_link"
    IMMEDIATE_RETRY = "immediate_retry"
    ESCALATE_MANUAL_REVIEW = "escalate_manual_review"
    STOP_NO_ACTION = "stop_no_action"


class DiagnosisSource(str, Enum):
    RULE = "rule"
    LLM = "llm"


class RecoveryOutcome(str, Enum):
    RECOVERED = "recovered"
    FAILED = "failed"
    PENDING = "pending"


class PaymentStatus(str, Enum):
    FAILED = "failed"
    RECOVERED = "recovered"
    ESCALATED = "escalated"
    STOPPED = "stopped"


class AuditEventType(str, Enum):
    DIAGNOSIS = "diagnosis"
    POLICY_DECISION = "policy_decision"
    RECOVERY_ATTEMPT = "recovery_attempt"
    ESCALATION = "escalation"
    STOP = "stop"
    RECOVERY = "recovery"
