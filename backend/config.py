import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "phi3:mini"
    app_port: int = 8000
    chroma_db_path: str = str(BASE_DIR / "chroma_db")

    model_config = {"env_file": str(BASE_DIR / ".env"), "extra": "ignore"}


settings = Settings()

BRAND_CONFIGS = {
    "ticket99": {
        "name": "Tickets99",
        "tagline": "India's Premier Event Ticketing Platform",
        "collection": "ticket99_knowledge",
        "prompt_file": str(BASE_DIR / "prompts" / "ticket99_system.txt"),
        "faq_file": str(BASE_DIR / "knowledge" / "ticket99_faqs.json"),
        "docs_dir": str(BASE_DIR / "knowledge" / "ticket99_docs"),
        "support_email": "support@tickets99.com",
        "support_phone": "+91 9876543210",
        "website": "https://www.tickets99.com",
        "primary_color": "#f97316",
        "secondary_color": "#ef4444",
    },
    "eventitans": {
        "name": "Eventitans",
        "tagline": "Full-Service Event Management Platform",
        "collection": "eventitans_knowledge",
        "prompt_file": str(BASE_DIR / "prompts" / "eventitans_system.txt"),
        "faq_file": str(BASE_DIR / "knowledge" / "eventitans_faqs.json"),
        "docs_dir": str(BASE_DIR / "knowledge" / "eventitans_docs"),
        "support_email": "support@eventitans.com",
        "support_phone": "",
        "website": "https://www.eventitans.com",
        "primary_color": "#6366f1",
        "secondary_color": "#8b5cf6",
    },
}

# Intent definitions - migrated from knowledge_base.py keyword lists
# Priority order matters: earlier intents are checked first
INTENT_DEFINITIONS = {
    "greeting": {
        "keywords": [
            "hi", "hello", "hey", "hii", "hiii", "howdy", "namaste",
            "good morning", "good afternoon", "good evening",
            "greetings", "sup", "yo", "heya", "hola", "hy",
        ],
        "priority": 1,
    },
    "farewell": {
        "keywords": [
            "bye", "goodbye", "see you", "see ya", "cya", "later",
            "gtg", "gotta go", "take care", "good night", "goodnight",
            "bye bye", "byebye",
        ],
        "priority": 2,
    },
    "gratitude": {
        "keywords": [
            "thanks", "thank you", "thank u", "thankyou", "thx", "ty",
            "tysm", "appreciate", "thanks a lot", "thanks so much",
        ],
        "priority": 3,
    },
    "refund": {
        "keywords": ["refund", "money back", "refund policy"],
        "priority": 4,
    },
    "cancel": {
        "keywords": ["cancel", "cancellation"],
        "priority": 5,
    },
    "pricing": {
        "keywords": [
            "price", "pricing", "cost", "fee", "fees", "commission",
            "charge", "charges", "how much", "expensive", "cheap",
            "free", "money", "subscription", "plans", "rate", "rates",
        ],
        "priority": 6,
    },
    "organizer": {
        "keywords": [
            "organize", "organizer", "organiser", "host", "hosting",
            "create event", "sell tickets", "start selling", "my event",
            "list event", "manage event", "event management",
            "event platform", "how to create",
        ],
        "priority": 7,
    },
    "attendee": {
        "keywords": [
            "buy ticket", "purchase ticket", "book ticket", "find event",
            "attend", "attending", "upcoming event", "events near",
            "browse event", "looking for event", "want to attend",
            "find tickets", "get tickets", "show me events",
        ],
        "priority": 8,
    },
    "partnership": {
        "keywords": [
            "partner", "partnership", "sponsor", "sponsorship",
            "collaborate", "collaboration", "b2b", "bulk",
            "reseller", "venue partnership", "corporate solutions",
        ],
        "priority": 9,
    },
    "support": {
        "keywords": [
            "support", "help me", "problem", "issue", "complaint",
            "not working", "bug", "error", "something went wrong",
            "broken", "doesnt work", "cant access",
        ],
        "priority": 10,
    },
    "contact": {
        "keywords": [
            "contact", "reach", "call", "phone", "email",
            "whatsapp", "address", "office",
        ],
        "priority": 11,
    },
    "features": {
        "keywords": [
            "feature", "features", "what do you offer",
            "services", "functionality", "capabilities",
        ],
        "priority": 12,
    },
    "about": {
        "keywords": [
            "what is tickets99", "about tickets99", "tell me about tickets99",
            "what does tickets99 do", "about your company", "about your platform",
            "what is eventitans", "about eventitans", "tell me about eventitans",
        ],
        "priority": 13,
    },
    "payment": {
        "keywords": [
            "payment", "pay", "upi", "card", "net banking",
            "stripe", "gpay", "paytm", "payment method",
            "how to pay", "payment options",
        ],
        "priority": 14,
    },
    "checkin": {
        "keywords": [
            "check-in", "checkin", "qr code", "qr",
            "scan", "entry", "barcode",
        ],
        "priority": 15,
    },
    "analytics": {
        "keywords": [
            "analytics", "dashboard", "reports",
            "insights", "statistics",
        ],
        "priority": 16,
    },
    "security": {
        "keywords": [
            "secure", "security", "safe", "trust",
            "reliable", "encryption", "privacy", "data protection",
        ],
        "priority": 17,
    },
    "getting_started": {
        "keywords": [
            "get started", "how to start", "sign up", "register",
            "create account", "onboard", "how do i begin",
            "how do i start", "getting started",
        ],
        "priority": 18,
    },
    "cities": {
        "keywords": [
            "which cities", "what cities", "where do you operate",
            "locations", "which city", "available cities",
            "where are you available", "which places",
            "hyderabad", "delhi", "mumbai", "bangalore", "bengaluru",
            "jaipur", "chennai", "noida",
        ],
        "priority": 19,
    },
    "discount": {
        "keywords": [
            "discount", "promo", "coupon", "offer",
            "early bird", "group discount", "promo code",
        ],
        "priority": 20,
    },
}


if __name__ == "__main__":
    print(f"Settings loaded: {settings}")
    print(f"Brands: {list(BRAND_CONFIGS.keys())}")
    print(f"Intents: {list(INTENT_DEFINITIONS.keys())}")
