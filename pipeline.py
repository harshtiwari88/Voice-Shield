from .risk_calculator import calculate_risk


def calculate_final_risk(
    voice_risk,
    context_risk,
    action_risk,
    reliability
):
    return calculate_risk(
        voice_risk=voice_risk,
        context_risk=context_risk,
        action_risk=action_risk,
        reliability=reliability
    )