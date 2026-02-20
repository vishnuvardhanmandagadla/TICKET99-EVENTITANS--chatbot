"""Tests to verify basic setup and imports work correctly."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_imports():
    """Verify all core modules can be imported."""
    import config
    import intent_classifier
    import vector_store
    import conversation_manager
    import rag_chain
    import api_integrations
    import whatsapp_handler


def test_settings_load():
    """Verify Settings loads without error."""
    from config import settings
    assert settings.app_port > 0
    assert settings.ollama_model
    assert settings.ollama_base_url.startswith("http")


def test_brand_configs():
    """Verify brand configs are valid."""
    from config import BRAND_CONFIGS

    assert "ticket99" in BRAND_CONFIGS
    assert "eventitans" in BRAND_CONFIGS

    for brand_key, config in BRAND_CONFIGS.items():
        assert config["name"], f"{brand_key} missing name"
        assert config["collection"], f"{brand_key} missing collection"
        assert config["prompt_file"], f"{brand_key} missing prompt_file"
        assert config["faq_file"], f"{brand_key} missing faq_file"
        assert Path(config["prompt_file"]).exists(), f"{brand_key} prompt file missing"
        assert Path(config["faq_file"]).exists(), f"{brand_key} faq file missing"


def test_intent_definitions():
    """Verify intent definitions are valid."""
    from config import INTENT_DEFINITIONS

    assert len(INTENT_DEFINITIONS) > 10
    for intent_name, intent_config in INTENT_DEFINITIONS.items():
        assert "keywords" in intent_config, f"{intent_name} missing keywords"
        assert "priority" in intent_config, f"{intent_name} missing priority"
        assert len(intent_config["keywords"]) > 0, f"{intent_name} has no keywords"


def test_faq_files_valid_json():
    """Verify FAQ JSON files are valid and have expected structure."""
    import json
    from config import BRAND_CONFIGS

    for brand_key, config in BRAND_CONFIGS.items():
        faq_path = Path(config["faq_file"])
        with open(faq_path, "r", encoding="utf-8") as f:
            faqs = json.load(f)

        assert isinstance(faqs, list), f"{brand_key} FAQs should be a list"
        assert len(faqs) > 10, f"{brand_key} should have >10 FAQs"

        for faq in faqs:
            assert "question" in faq, f"{brand_key} FAQ missing question"
            assert "answer" in faq, f"{brand_key} FAQ missing answer"
            assert "category" in faq, f"{brand_key} FAQ missing category"
