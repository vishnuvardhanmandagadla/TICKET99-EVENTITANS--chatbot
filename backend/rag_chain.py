import traceback
import httpx
from pathlib import Path

from config import settings, BRAND_CONFIGS
from intent_classifier import classify_intent
from vector_store import search as vector_search
from conversation_manager import get_recent_history

# Try langdetect, fall back gracefully
try:
    from langdetect import detect as _detect_lang
except ImportError:
    _detect_lang = None


def detect_language(text: str) -> str:
    """Detect language of user message. Returns ISO 639-1 code."""
    if _detect_lang is None:
        return "en"
    try:
        lang = _detect_lang(text)
        return lang
    except Exception:
        return "en"


def _load_system_prompt(brand: str) -> str:
    """Load the system prompt from file for a brand."""
    brand_config = BRAND_CONFIGS.get(brand, {})
    prompt_file = brand_config.get("prompt_file", "")
    path = Path(prompt_file)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"You are a helpful assistant for {brand_config.get('name', brand)}."


def _build_prompt(
    brand: str,
    user_message: str,
    session_id: str,
    intent: str | None,
    language: str,
    rag_context: list[dict],
) -> list[dict[str, str]]:
    """Assemble the full prompt for the LLM."""
    system_prompt = _load_system_prompt(brand)

    # Add RAG context
    if rag_context:
        context_text = "\n\nRelevant information from our knowledge base:\n"
        for i, chunk in enumerate(rag_context, 1):
            if chunk["question"]:
                context_text += f"{i}. Q: {chunk['question']}\n   A: {chunk['answer']}\n"
            else:
                context_text += f"{i}. {chunk['answer']}\n"
        system_prompt += context_text

    # Add intent hint
    if intent:
        system_prompt += f"\n\nDetected user intent: {intent}. Tailor your response accordingly."

    # Add language instruction
    if language != "en":
        system_prompt += f"\n\nIMPORTANT: The user is writing in '{language}'. You MUST respond in the same language."

    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history
    history = get_recent_history(session_id)
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    return messages


def _fallback_response(brand: str, user_message: str, rag_context: list[dict], intent: str | None) -> str:
    """Generate a smart response without the LLM.
    Uses intent classification first, then best RAG match."""
    brand_config = BRAND_CONFIGS.get(brand, {})
    brand_name = brand_config.get("name", brand)
    website = brand_config.get("website", "")
    email = brand_config.get("support_email", "")

    # --- Intent-specific responses take priority ---
    if intent == "greeting":
        return f"Hello! Welcome to {brand_name}. How can I help you today? You can ask me about events, pricing, features, or partnerships!"

    if intent == "farewell":
        return f"Goodbye! Visit {website} anytime. Have a great day!"

    if intent == "gratitude":
        return f"You're welcome! Let me know if you have more questions about {brand_name}."

    if intent == "support":
        return f"I'm sorry to hear that! Please reach our support team at {email} and they'll help you sort it out."

    if intent == "contact":
        phone = brand_config.get("support_phone", "")
        return f"You can reach us at {email}" + (f" or call {phone}" if phone else "") + ". Our team usually responds within a few hours!"

    if intent == "refund":
        return f"Refund policies are set by each event organizer. Check the event page for details, or email {email} with your booking ID and we'll help sort it out."

    if intent == "cancel":
        return f"To cancel a ticket, check the event page for the cancellation policy. You can also email {email} with your booking details and we'll assist you."

    if intent == "pricing":
        if brand == "ticket99":
            return "Tickets99 pricing is simple: free to list events, 2-5% commission on ticket sales only. Payment processing is 2% + GST. Zero upfront costs!"
        else:
            return "We offer three tiers: Starter (Free) - up to 3 events/month; Pro (Rs 2,999/month) - unlimited events with advanced features; Enterprise (Custom) - white-label solution with dedicated support."

    if intent == "organizer":
        return f"{brand_name} makes it easy to organize events! Free to start, quick setup, and powerful tools. What type of event are you planning?"

    if intent == "attendee":
        return f"You can browse and buy tickets at {website}! We have events across multiple cities. Any specific event type you're looking for?"

    if intent == "partnership":
        return f"We'd love to explore partnerships! Tell me more about what kind of collaboration you're interested in - sponsorship, venue, corporate, or reseller?"

    if intent == "features":
        if brand == "ticket99":
            return "Key features: online ticketing, QR code check-in, real-time analytics, mobile app, discount codes, and direct bank payments. Which feature interests you?"
        else:
            return "Key features: event planning tools, venue management, vendor marketplace, budget tracking, team collaboration, marketing automation, and analytics dashboard."

    if intent == "about":
        if brand == "ticket99":
            return "Tickets99 is India's premier event ticketing platform. 1,999+ events hosted, 499,999+ attendees, 599+ organizers across 7+ cities. Want to know about our features or pricing?"
        else:
            return "Eventitans is a full-service event management platform providing end-to-end tools for planning, venues, vendors, budgets, marketing, and analytics."

    if intent == "getting_started":
        return f"Just head to {website}, sign up for free, and get started! It takes under 5 minutes. Want me to help you with anything specific?"

    if intent == "cities":
        if brand == "ticket99":
            return "We're active in Hyderabad, Delhi, Mumbai, Bangalore, Jaipur, Chennai, and Noida - with more cities coming soon! Which city are you in?"

    if intent == "checkin":
        return "Every ticket gets a unique QR code. Organizers can scan it with our mobile app for instant check-in at the venue. Fast, secure, and no duplicate entries!"

    if intent == "payment":
        return "We support UPI, credit/debit cards, net banking, and digital wallets. Payments are processed securely through trusted payment partners."

    if intent == "analytics":
        return "We provide a real-time analytics dashboard showing ticket sales, revenue, attendee demographics, and marketing insights. All included with your account!"

    if intent == "security":
        return "We use industry-standard encryption for all transactions. Payment data is processed securely and never stored on our servers."

    if intent == "discount":
        return "Organizers can create unlimited discount codes, early bird pricing, group discounts, and special promos. All built into the platform!"

    # --- If no intent matched, use best RAG match ---
    if rag_context:
        best = rag_context[0]
        return best["answer"]

    # --- Generic fallback ---
    return f"I can help you with {brand_name}! Ask me about events, pricing, features, or how to get started."


# Persistent HTTP client (reused across requests)
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=90.0, write=10.0, pool=10.0)
        )
    return _http_client


async def generate_response(
    brand: str,
    user_message: str,
    session_id: str,
) -> str:
    """Core RAG pipeline: detect language -> classify intent -> search vectors -> call LLM.

    Falls back to intent-based response if Ollama is unavailable.
    """
    # Step 1: Detect language
    language = detect_language(user_message)

    # Step 2: Classify intent
    intent, confidence = classify_intent(user_message)

    # Step 3: Search vector store for relevant context
    rag_context = vector_search(brand, user_message, top_k=3)

    # Step 4: Build prompt and call Ollama
    messages = _build_prompt(brand, user_message, session_id, intent, language, rag_context)

    try:
        client = _get_http_client()
        response = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 256,
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        answer = data.get("message", {}).get("content", "").strip()
        if answer:
            return answer
        print("  [WARN] Ollama returned empty response, using fallback")
    except Exception as e:
        print(f"  [WARN] Ollama error: {type(e).__name__}: {e}")
        traceback.print_exc()

    # Fallback: use intent-based response
    return _fallback_response(brand, user_message, rag_context, intent)


async def check_ollama_health() -> bool:
    """Check if Ollama is reachable."""
    try:
        client = _get_http_client()
        resp = await client.get(f"{settings.ollama_base_url}/api/tags")
        return resp.status_code == 200
    except Exception:
        return False
