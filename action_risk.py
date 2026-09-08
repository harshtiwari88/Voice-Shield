ACTION_RISK = {
    "financial_request": 0.90,
    "credential_request": 0.85,
    "verification_bypass": 0.80,
    "urgent_request": 0.40,
    "authority_claim": 0.30
}


def calculate_action_risk(indicators):
    if not indicators:
        return 0.10

    risk = max(
        ACTION_RISK.get(indicator, 0)
        for indicator in indicators
    )

    return risk


if __name__ == "__main__":

    test_indicators = [
        "financial_request",
        "urgent_request",
        "verification_bypass",
        "authority_claim"
    ]

    action_risk = calculate_action_risk(test_indicators)

    print("Action Risk:", action_risk)