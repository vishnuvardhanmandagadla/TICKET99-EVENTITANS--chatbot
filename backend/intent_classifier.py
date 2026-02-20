import re
from config import INTENT_DEFINITIONS


def _has_keyword(text: str, words: set, keywords: list[str]) -> bool:
    """Check if any keyword matches using word boundaries for single words,
    or substring match for multi-word phrases.
    Ported from knowledge_base.py:493-503."""
    for kw in keywords:
        if " " in kw:
            if kw in text:
                return True
        else:
            if re.search(r"\b" + re.escape(kw) + r"\b", text):
                return True
    return False


def classify_intent(message: str) -> tuple[str | None, float]:
    """Classify user message intent using keyword matching.

    Returns (intent_name, confidence) or (None, 0.0) if no match.
    Priority ordering ensures greeting > refund > pricing > organizer > support > general.
    """
    lower = message.lower().strip()
    clean = re.sub(r"[^\w\s]", "", lower).strip()
    words = set(clean.split())

    # Sort intents by priority
    sorted_intents = sorted(
        INTENT_DEFINITIONS.items(), key=lambda x: x[1]["priority"]
    )

    for intent_name, intent_config in sorted_intents:
        keywords = intent_config["keywords"]
        if _has_keyword(lower, words, keywords):
            # Higher priority intents get higher confidence
            confidence = max(0.5, 1.0 - (intent_config["priority"] - 1) * 0.02)
            return intent_name, confidence

    return None, 0.0


if __name__ == "__main__":
    test_messages = [
        "hello",
        "how much does it cost?",
        "I want a refund",
        "how do I organize an event?",
        "tell me about partnerships",
        "what is the weather today?",
        "I want to buy tickets",
        "where are you available?",
    ]
    for msg in test_messages:
        intent, conf = classify_intent(msg)
        print(f"  '{msg}' -> intent={intent}, confidence={conf:.2f}")
