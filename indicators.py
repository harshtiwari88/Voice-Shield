FINANCIAL_TERMS = [
    "transfer money",
    "transfer ₹",
    "send money",
    "make a payment",
    "bank transfer",
    "wire transfer",
    "transaction",
    "send ₹",
    "pay"
]

CREDENTIAL_TERMS = [
    "otp",
    "password",
    "pin",
    "verification code",
    "security code"
]

URGENCY_TERMS = [
    "immediately",
    "urgent",
    "right now",
    "quickly",
    "as soon as possible"
]

BYPASS_TERMS = [
    "don't call me back",
    "do not call me back",
    "don't tell anyone",
    "do not tell anyone",
    "skip verification",
    "keep this confidential"
]

AUTHORITY_TERMS = [
    "ceo",
    "manager",
    "director",
    "boss",
    "senior",
    "supervisor"
]


INDICATOR_WEIGHTS = {
    "financial_request": 0.25,
    "credential_request": 0.30,
    "urgent_request": 0.15,
    "verification_bypass": 0.25,
    "authority_claim": 0.10
}


def detect_indicators(transcript):
    text = transcript.lower()

    indicators = []

    if any(term in text for term in FINANCIAL_TERMS):
        indicators.append("financial_request")

    if any(term in text for term in CREDENTIAL_TERMS):
        indicators.append("credential_request")

    if any(term in text for term in URGENCY_TERMS):
        indicators.append("urgent_request")

    if any(term in text for term in BYPASS_TERMS):
        indicators.append("verification_bypass")

    if any(term in text for term in AUTHORITY_TERMS):
        indicators.append("authority_claim")

    return indicators


def calculate_context_risk(indicators):
    score = sum(INDICATOR_WEIGHTS.get(i, 0) for i in indicators)
    return min(score, 1.0)


if __name__ == "__main__":

    transcript = """
    I'm your CEO. I'm in a meeting.
    Transfer ₹20 lakh immediately.
    Don't call me back because I cannot answer.
    """

    indicators = detect_indicators(transcript)
    context_risk = calculate_context_risk(indicators)

    print("Detected Indicators:")

    for indicator in indicators:
        print("-", indicator)

    print("\nContext Risk:", round(context_risk, 3))