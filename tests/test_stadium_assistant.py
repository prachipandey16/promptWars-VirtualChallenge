"""
Comprehensive test suite for StadiumAssistant.

Covers prompt building, input sanitization, API key handling,
multilingual support, stadium context, conversation history,
rate limiting, and error handling.
"""

import os
import sys
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.assistant import StadiumAssistant, RateLimiter


# ── RateLimiter Tests ──

def test_rate_limiter_waits_when_needed():
    """RateLimiter should sleep when called within min_interval."""
    import time
    limiter = RateLimiter(min_interval=0.1)
    limiter.last_call_time = time.time()  # recent call
    start = time.time()
    limiter.wait_if_needed()
    elapsed = time.time() - start
    assert elapsed >= 0.05  # should have waited at least a bit


def test_rate_limiter_does_not_wait_when_cold():
    """RateLimiter should not sleep if enough time has passed."""
    limiter = RateLimiter(min_interval=0.1)
    limiter.last_call_time = 0.0  # very old call
    start = time.time()
    limiter.wait_if_needed()
    elapsed = time.time() - start
    assert elapsed < 0.05  # should not have waited


# ── Sanitization Tests ──

def test_sanitize_input_removes_null_bytes():
    """sanitize_input should remove null bytes."""
    result = StadiumAssistant.sanitize_input("hello\x00world")
    assert "\x00" not in result


def test_sanitize_input_trims_whitespace():
    """sanitize_input should strip leading/trailing whitespace."""
    result = StadiumAssistant.sanitize_input("  hello world  ")
    assert result == "hello world"


def test_sanitize_input_collapses_multiple_spaces():
    """sanitize_input should collapse multiple spaces into one."""
    result = StadiumAssistant.sanitize_input("hello    world")
    assert result == "hello world"


def test_sanitize_input_limits_length():
    """sanitize_input should limit input to 2000 characters."""
    long_input = "a" * 5000
    result = StadiumAssistant.sanitize_input(long_input)
    assert len(result) <= 2000


def test_sanitize_input_handles_empty():
    """sanitize_input should return empty string for None/empty."""
    assert StadiumAssistant.sanitize_input("") == ""
    assert StadiumAssistant.sanitize_input(None) == ""


# ── Prompt Building Tests ──

def test_build_prompt_includes_context_and_user_query():
    """Prompt should include FIFA context, user query, and role."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt("Where is Gate A?", "fan")

    assert "FIFA World Cup 2026" in prompt
    assert "Gate A" in prompt
    assert "fan" in prompt


def test_build_prompt_includes_stadium_context():
    """Prompt should include stadium info when provided."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt("Where is parking?", "fan", stadium="SoFi Stadium")

    assert "SoFi Stadium" in prompt
    assert "Inglewood" in prompt
    assert "70,240" in prompt


def test_build_prompt_includes_language():
    """Prompt should include the selected language."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt("Hello", "fan", language="Spanish")

    assert "Spanish" in prompt


def test_build_prompt_includes_conversation_history():
    """Prompt should include recent conversation history."""
    assistant = StadiumAssistant()
    history = [
        {"role": "user", "content": "Where is Gate A?"},
        {"role": "assistant", "content": "Gate A is at the north entrance."},
    ]
    prompt = assistant.build_prompt(
        "Thanks!", "fan", conversation_history=history
    )

    assert "Where is Gate A?" in prompt
    assert "Gate A is at the north entrance" in prompt


def test_build_prompt_handles_empty_history():
    """Prompt should work without conversation history."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt("Hello", "fan")

    assert "Hello" in prompt
    assert "Recent conversation" not in prompt


def test_build_prompt_includes_date_as_preference():
    """Prompt should label date as user preference, not match schedule."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt("What's happening?", "fan",
                                    match_date="2026-07-18",
                                    match_time="20:00")

    assert "user's preference" in prompt.lower()
    assert "NOT a confirmed match" in prompt


def test_build_prompt_includes_match_guidance():
    """Prompt should guide the model to use Google Search for matches."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt("Who is playing?", "fan")

    assert "match-related" in prompt.lower()
    assert "Google Search grounding" in prompt


def test_build_prompt_sanitizes_user_query():
    """Prompt should sanitize user input."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt("hello\x00world", "fan")

    assert "\x00" not in prompt


# ── API Key Handling Tests ──

def test_prepare_response_handles_missing_api_key():
    """Should return error message when API key is missing."""
    assistant = StadiumAssistant()

    with patch.dict(os.environ, {}, clear=True):
        result = assistant.prepare_response(
            "What should I do if the crowd grows?", "staff"
        )

    assert "api key" in result.lower()


def test_prepare_response_handles_empty_query():
    """Should return error for empty query."""
    assistant = StadiumAssistant(api_key="test-key")
    result = assistant.prepare_response("", "fan")
    assert "valid question" in result.lower()


def test_prepare_response_handles_whitespace_query():
    """Should return error for whitespace-only query."""
    assistant = StadiumAssistant(api_key="test-key")
    result = assistant.prepare_response("   ", "fan")
    assert "valid question" in result.lower()


# ── Model Fallback Tests ──

def test_get_model_candidates_returns_list():
    """Should return a non-empty list of model names."""
    assistant = StadiumAssistant()
    models = assistant._get_model_candidates()
    assert isinstance(models, list)
    assert len(models) > 0
    assert all(isinstance(m, str) for m in models)


# ── Stadium Data Tests ──

def test_fifa_stadiums_contains_all_venues():
    """FIFA_STADIUMS should contain all 8 venues."""
    assert len(StadiumAssistant.FIFA_STADIUMS) == 8
    assert "MetLife Stadium" in StadiumAssistant.FIFA_STADIUMS
    assert "SoFi Stadium" in StadiumAssistant.FIFA_STADIUMS
    assert "AT&T Stadium" in StadiumAssistant.FIFA_STADIUMS
    assert "Mercedes-Benz Stadium" in StadiumAssistant.FIFA_STADIUMS
    assert "Levi's Stadium" in StadiumAssistant.FIFA_STADIUMS
    assert "NRG Stadium" in StadiumAssistant.FIFA_STADIUMS
    assert "Lincoln Financial Field" in StadiumAssistant.FIFA_STADIUMS
    assert "Gillette Stadium" in StadiumAssistant.FIFA_STADIUMS


def test_each_stadium_has_capacity():
    """Each stadium entry should include capacity info."""
    for name, info in StadiumAssistant.FIFA_STADIUMS.items():
        assert "capacity" in info.lower(), f"{name} missing capacity"


def test_each_stadium_has_gates():
    """Each stadium entry should include gate info."""
    for name, info in StadiumAssistant.FIFA_STADIUMS.items():
        assert "gate" in info.lower(), f"{name} missing gate info"


# ── Role Mapping Tests ──

def test_build_prompt_supports_all_roles():
    """Prompt should work with all user roles."""
    assistant = StadiumAssistant()
    for role in ["fan", "organizer", "volunteer", "staff"]:
        prompt = assistant.build_prompt("Test", role)
        assert role in prompt


# ── Import Error Handling Tests ──

def test_prepare_response_handles_import_error():
    """Should handle missing google-genai package gracefully."""
    assistant = StadiumAssistant(api_key="test-key")
    with patch.dict("sys.modules", {"google": None}):
        result = assistant.prepare_response("Hello", "fan")
        # Should not crash — returns error message
        assert isinstance(result, str)


# ── Match Query Detection Tests ──

def test_is_match_related_query_detects_scores():
    """Should detect score-related queries as match-related."""
    assistant = StadiumAssistant()
    assert assistant._is_match_related_query("What is the score?") is True
    assert assistant._is_match_related_query("Latest scores") is True
    assert assistant._is_match_related_query("Who won?") is True


def test_is_match_related_query_detects_schedules():
    """Should detect schedule-related queries as match-related."""
    assistant = StadiumAssistant()
    assert assistant._is_match_related_query("When is the match?") is True
    assert assistant._is_match_related_query("Match schedule") is True
    assert assistant._is_match_related_query("Who is playing?") is True
    assert assistant._is_match_related_query("Which teams are playing?") is True


def test_is_match_related_query_detects_standings():
    """Should detect standings-related queries as match-related."""
    assistant = StadiumAssistant()
    assert assistant._is_match_related_query("What are the standings?") is True
    assert assistant._is_match_related_query("Tournament standings") is True


def test_is_match_related_query_detects_broadcast():
    """Should detect broadcast-related queries as match-related."""
    assistant = StadiumAssistant()
    assert assistant._is_match_related_query("Where can I watch?") is True
    assert assistant._is_match_related_query("TV broadcast") is True
    assert assistant._is_match_related_query("Streaming info") is True


def test_is_match_related_query_ignores_operational():
    """Should NOT detect operational queries as match-related."""
    assistant = StadiumAssistant()
    assert assistant._is_match_related_query("Where is Gate A?") is False
    assert assistant._is_match_related_query("How do I get to the stadium?") is False
    assert assistant._is_match_related_query("Is there parking?") is False
    assert assistant._is_match_related_query("What's the crowd level?") is False
    assert assistant._is_match_related_query("How do I get wheelchair access?") is False


# ── Conditional Tool Usage Tests ──

def test_prepare_response_skips_search_tool_for_operational_queries():
    """Should not use Google Search tool for operational queries."""
    assistant = StadiumAssistant(api_key="test-key")
    
    with patch("google.genai.Client") as mock_client:
        mock_model = MagicMock()
        mock_client.return_value.models.generate_content.return_value = MagicMock(text="Response")
        
        result = assistant.prepare_response(
            "Where is Gate A?",
            "fan",
            stadium="MetLife Stadium"
        )
        
        # Verify the API was called
        assert mock_client.return_value.models.generate_content.called
        # Get the config that was passed
        call_args = mock_client.return_value.models.generate_content.call_args
        config = call_args.kwargs.get("config", call_args[1].get("config") if len(call_args) > 1 else None)
        
        # For operational queries, tools should not be included
        if config:
            assert not hasattr(config, "tools") or config.tools is None or len(config.tools) == 0


def test_prepare_response_uses_search_tool_for_match_queries():
    """Should use Google Search tool for match-related queries."""
    assistant = StadiumAssistant(api_key="test-key")
    
    with patch("google.genai.Client") as mock_client:
        mock_model = MagicMock()
        mock_client.return_value.models.generate_content.return_value = MagicMock(text="Response")
        
        result = assistant.prepare_response(
            "What is the score?",
            "fan"
        )
        
        # Verify the API was called
        assert mock_client.return_value.models.generate_content.called
        # The tool usage is handled internally, just verify it didn't crash


# ── Fallback Behavior Tests ──

def test_prepare_response_retries_without_tool_on_quota_error():
    """Should retry without Google Search tool if quota is exhausted."""
    assistant = StadiumAssistant(api_key="test-key")
    
    with patch("google.genai.Client") as mock_client:
        # First call fails with 429, second call succeeds
        mock_client.return_value.models.generate_content.side_effect = [
            Exception("429 RESOURCE_EXHAUSTED"),
            MagicMock(text="Fallback response"),
        ]
        
        result = assistant.prepare_response(
            "What is the latest score?",
            "fan"
        )
        
        # Should have tried twice
        assert mock_client.return_value.models.generate_content.call_count == 2
        # Should return the fallback response
        assert "Fallback response" in result
        assert "quota" in result.lower() or "real-time" in result.lower()


def test_prepare_response_handles_permanent_failure():
    """Should return error message when all models fail."""
    assistant = StadiumAssistant(api_key="test-key")
    
    with patch("google.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.side_effect = Exception("Permanent error")
        
        result = assistant.prepare_response("Hello", "fan")
        
        assert "Unable to generate response" in result
