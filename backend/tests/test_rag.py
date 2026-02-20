"""Tests for intent classification, vector store search, and prompt assembly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_intent_greeting():
    from intent_classifier import classify_intent
    intent, conf = classify_intent("hello")
    assert intent == "greeting"
    assert conf > 0.5


def test_intent_pricing():
    from intent_classifier import classify_intent
    intent, conf = classify_intent("how much does it cost?")
    assert intent == "pricing"
    assert conf > 0.5


def test_intent_refund():
    from intent_classifier import classify_intent
    intent, conf = classify_intent("I want a refund")
    assert intent == "refund"
    assert conf > 0.5


def test_intent_organizer():
    from intent_classifier import classify_intent
    intent, conf = classify_intent("I want to organize an event")
    assert intent == "organizer"


def test_intent_partnership():
    from intent_classifier import classify_intent
    intent, conf = classify_intent("I'm interested in sponsorship")
    assert intent == "partnership"


def test_intent_none_for_random():
    from intent_classifier import classify_intent
    intent, conf = classify_intent("tell me a joke about cats")
    # Should not match any intent
    assert intent is None or conf < 0.9


def test_word_boundary_no_false_positive():
    """Ensure 'rate' doesn't match inside 'integrate'."""
    from intent_classifier import _has_keyword
    assert not _has_keyword("integrate with api", set(), ["rate"])
    assert _has_keyword("what is the rate", set(), ["rate"])


def test_phrase_matching():
    """Multi-word phrases use substring matching."""
    from intent_classifier import _has_keyword
    assert _has_keyword("how much does it cost", set(), ["how much"])
    assert not _has_keyword("howmuch", set(), ["how much"])


def test_vector_store_initialize_and_search():
    """Verify vector store can initialize and return results."""
    import vector_store

    vector_store.initialize()

    results = vector_store.search("ticket99", "how much does it cost?")
    assert len(results) > 0
    assert "answer" in results[0]
    assert results[0]["distance"] <= 1.5

    results_et = vector_store.search("eventitans", "how do I plan an event?")
    assert len(results_et) > 0


def test_conversation_manager():
    from conversation_manager import (
        add_message, get_recent_history, get_message_count,
        clear_session, get_or_create_session,
    )

    sid = "test_session_123"
    get_or_create_session(sid)
    add_message(sid, "user", "hello")
    add_message(sid, "assistant", "Hi there!")
    add_message(sid, "user", "pricing?")

    history = get_recent_history(sid)
    assert len(history) == 3
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "hello"

    assert get_message_count(sid, "user") == 2

    clear_session(sid)
    assert get_recent_history(sid) == []
