def classify_risk(final_score):

    if final_score >= 0.80:
        return "CRITICAL", "HOLD_AND_VERIFY"

    elif final_score >= 0.60:
        return "HIGH", "VERIFY"

    elif final_score >= 0.35:
        return "MEDIUM", "WARNING"

    else:
        return "LOW", "CONTINUE"


def calculate_risk(
    voice_risk,
    context_risk,
    action_risk,
    reliability
):
    reliability_risk = 1 - reliability

    final_score = (
        voice_risk * 0.35
        + context_risk * 0.25
        + action_risk * 0.30
        + reliability_risk * 0.10
    )

    risk_level, action = classify_risk(final_score)

    return {
        "final_risk": round(final_score, 3),
        "risk_level": risk_level,
        "action": action
    }


if __name__ == "__main__":
    result = calculate_risk(
        voice_risk=0.87,
        context_risk=0.82,
        action_risk=0.95,
        reliability=0.72
    )

    print(result)