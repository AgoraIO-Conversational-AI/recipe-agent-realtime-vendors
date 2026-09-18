import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import vendors as R  # noqa: E402

# vendors whose to_config() emits a "vendor" key, and the expected value
EXPECTED_VENDOR = {
    "openai": "openai",
    "openai_gpt_live": "openai_gpt_live",
    "azure": "azure",
    "gemini": "gemini",
    "xai": "xai",
    "vertexai": "vertexai",
}


def _dummy_env(name):
    return {var: "dummy" for var in R.required_env(name)}


def test_every_vendor_constructs_and_emits_config():
    for name in R.available():
        vendor = R.build_vendor(name, _dummy_env(name))
        cfg = vendor.to_config()
        assert isinstance(cfg, dict) and cfg, f"{name}: empty config"
        if name in EXPECTED_VENDOR:
            assert cfg.get("vendor") == EXPECTED_VENDOR[name], f"{name}: vendor mismatch"


def test_byo_vendor_missing_creds_raises():
    byo = [n for n in R.available() if R.required_env(n)]
    assert byo, "expected at least one BYO vendor"
    name = byo[0]
    try:
        R.build_vendor(name, {})
    except ValueError as e:
        assert R.required_env(name)[0] in str(e)
    else:
        raise AssertionError(f"{name} should raise when creds are absent")


def test_azure_openai_realtime_uses_the_required_deployment_settings():
    config = R.build_vendor(
        "azure",
        {
            "AZURE_OPENAI_API_KEY": "azure-key",
            "AZURE_OPENAI_REALTIME_URL": "wss://example.openai.azure.com/openai/realtime",
            "AZURE_OPENAI_REALTIME_MODEL": "gpt-realtime-2",
        },
    ).to_config()
    assert config["vendor"] == "azure"
    assert config["url"] == "wss://example.openai.azure.com/openai/realtime"
    assert config["params"] == {
        "model": "gpt-realtime-2",
        "voice": "alloy",
        "instructions": "You are a Conversational AI Agent, developed by Agora.",
    }
    assert config["output_modalities"] == ["audio"]
    assert config["max_history"] == 20


def test_openai_realtime_uses_production_model_by_default():
    config = R.build_vendor("openai", {"OPENAI_API_KEY": "openai-key"}).to_config()
    assert config["params"]["model"] == "gpt-realtime"


def test_openai_gpt_live_uses_production_vendor_and_model():
    config = R.build_vendor(
        "openai_gpt_live", {"OPENAI_API_KEY": "openai-key"}
    ).to_config()
    assert config["vendor"] == "openai_gpt_live"
    assert config["url"] == "wss://api.openai.com/v1/live/sessions"
    assert config["params"]["model"] == "gpt-live-1"
    assert "turn_detection" not in config


def test_openai_model_override_does_not_leak_to_other_vendors():
    shared_env = {
        "OPENAI_API_KEY": "openai-key",
        "GEMINI_API_KEY": "gemini-key",
        "OPENAI_REALTIME_MODEL": "gpt-realtime",
    }
    gpt_live = R.build_vendor("openai_gpt_live", shared_env).to_config()
    gemini = R.build_vendor("gemini", shared_env).to_config()

    assert gpt_live["params"]["model"] == "gpt-live-1"
    assert gemini["params"]["model"] == R.GeminiLiveModels.LIVE_38


def test_gemini_live_uses_38_model_by_default():
    config = R.build_vendor("gemini", {"GEMINI_API_KEY": "gemini-key"}).to_config()
    assert config["vendor"] == "gemini"
    assert config["params"]["model"] == R.GeminiLiveModels.LIVE_38
    assert config["url"] == "https://generativelanguage.googleapis.com"


def test_gemini_extended_thinking_options_are_forwarded():
    config = R.build_vendor(
        "gemini",
        {
            "GEMINI_API_KEY": "gemini-key",
            "GEMINI_LIVE_MODEL": R.GeminiLiveModels.LIVE_38_EXTENDED_THINKING,
            "GEMINI_THINKING_LEVEL": "high",
        },
    ).to_config()
    assert config["params"]["model"] == R.GeminiLiveModels.LIVE_38_EXTENDED_THINKING
    assert config["params"]["thinking_level"] == "high"
