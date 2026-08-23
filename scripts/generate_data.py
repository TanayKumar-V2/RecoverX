from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd


SEED = 42
NUM_PAYMENTS = 300

OUTPUT_PATH = Path("data/synthetic_payments.csv")

DECLINE_DISTRIBUTION = {
    "insufficient_funds": 0.35,
    "expired_card": 0.20,
    "do_not_honor": 0.15,
    "network_error": 0.10,
    "fraud_suspected": 0.10,
    "ambiguous": 0.10,
}

SUBSCRIPTION_PLANS = {
    "monthly": 0.75,
    "annual": 0.25,
}

CURRENCY = "INR"


def choose_decline_code(rng: random.Random) -> str:
    values = list(DECLINE_DISTRIBUTION.keys())
    weights = list(DECLINE_DISTRIBUTION.values())

    return rng.choices(
        population=values,
        weights=weights,
        k=1,
    )[0]


def choose_subscription_plan(rng: random.Random) -> str:
    values = list(SUBSCRIPTION_PLANS.keys())
    weights = list(SUBSCRIPTION_PLANS.values())

    return rng.choices(
        population=values,
        weights=weights,
        k=1,
    )[0]


def generate_amount(
    np_rng: np.random.Generator,
) -> float:
    """
    Generate realistic subscription amounts.

    A log-normal distribution gives us many smaller
    subscriptions and fewer expensive ones.
    """

    amount = np_rng.lognormal(
        mean=np.log(1500),
        sigma=0.75,
    )

    amount = np.clip(
        amount,
        199,
        15_000,
    )

    return round(float(amount), 2)


def generate_tenure_months(
    rng: random.Random,
) -> int:
    return rng.randint(1, 72)


def generate_retry_count(
    rng: random.Random,
    decline_code: str,
) -> int:

    if decline_code == "fraud_suspected":
        return rng.randint(0, 1)

    if decline_code == "network_error":
        return rng.randint(0, 2)

    return rng.randint(0, 3)


def generate_failed_at(
    rng: random.Random,
) -> datetime:

    now = datetime.now(timezone.utc)

    days_ago = rng.randint(0, 30)
    hours_ago = rng.randint(0, 23)

    return now - timedelta(
        days=days_ago,
        hours=hours_ago,
    )


def generate_payment(
    rng: random.Random,
    np_rng: np.random.Generator,
) -> dict[str, object]:

    decline_code = choose_decline_code(rng)

    return {
        "payment_id": str(uuid4()),
        "customer_id": f"CUST-{rng.randint(10_000, 99_999)}",
        "amount": generate_amount(np_rng),
        "currency": CURRENCY,
        "decline_code": decline_code,
        "customer_tenure_months": generate_tenure_months(rng),
        "past_retry_count": generate_retry_count(
            rng,
            decline_code,
        ),
        "failed_at": generate_failed_at(rng).isoformat(),
        "subscription_plan": choose_subscription_plan(rng),
    }


def inject_tricky_cases(
    df: pd.DataFrame,
) -> pd.DataFrame:

    # Case 1:
    # Fraud with a high retry count.
    # The policy engine must still hard-stop it.
    df.loc[0, "decline_code"] = "fraud_suspected"
    df.loc[0, "past_retry_count"] = 3

    # Case 2:
    # A valid retry action that has already hit
    # the smart-retry limit.
    df.loc[1, "decline_code"] = "insufficient_funds"
    df.loc[1, "past_retry_count"] = 3

    # Case 3:
    # Ambiguous case intended for Cohere with
    # confusing customer context.
    df.loc[2, "decline_code"] = "do_not_honor"
    df.loc[2, "customer_tenure_months"] = 60
    df.loc[2, "past_retry_count"] = 2

    # Case 4:
    # New customer + ambiguous decline.
    df.loc[3, "decline_code"] = "do_not_honor"
    df.loc[3, "customer_tenure_months"] = 1
    df.loc[3, "past_retry_count"] = 0

    # Case 5:
    # Expired card should deterministically receive
    # the update-link action.
    df.loc[4, "decline_code"] = "expired_card"
    df.loc[4, "past_retry_count"] = 1

    return df


def generate_dataset() -> pd.DataFrame:
    rng = random.Random(SEED)
    np_rng = np.random.default_rng(SEED)

    rows = [generate_payment(rng, np_rng) for _ in range(NUM_PAYMENTS)]

    df = pd.DataFrame(rows)

    df = inject_tricky_cases(df)

    return df


def main() -> None:
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = generate_dataset()

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(f"Generated {len(df)} payments at {OUTPUT_PATH}")

    print("\nDecline distribution:")
    print(df["decline_code"].value_counts())

    print("\nTotal at-risk revenue:")
    print(f"₹{df['amount'].sum():,.2f}")


if __name__ == "__main__":
    main()
