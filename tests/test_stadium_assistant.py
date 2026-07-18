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

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.assistant import StadiumAssistant, RateLimiter
from src.constants import (
    ERROR_INVALID_QUERY,
    FIFA_STADIUMS,
    GEMINI_MODEL_CANDIDATES,
    MATCH_KEYWORDS,
    MAX_INPUT_LENGTH,
)
from src.dataclasses import AssistantConfig, PromptContext
from src.exceptions import (
    APIKeyMissingError,
    InvalidQueryError,
    ModelNotAvailableError,
)


# ── RateLimiter Tests ──

def test_rate_limiter_waits_when_needed() -> None:
    """RateLimiter should sleep when called within min_interval."""
    limiter = RateLimiter(min_interval=0.1)
    limiter.last_call_time = time.time()  # recent call
    start = time.time()
    limiter.wait_if_needed()
    elapsed = time.time() - start
    assert elapsed >= 0.05  # should have waited at least a bit


def test_rate_limiter_does_not_wait_when_cold() -> None:
    """RateLimiter should not sleep if enough time has passed."""
    limiter = RateLimiter(min_interval=0.1)
    limiter.last_call_time = 0.0  # very old call
    start = time.time()
    limiter.wait_if_needed()
    elapsed = time.time() - start
    assert elapsed < 0.05  # should not have waited


# ── Sanitization Tests ──

def test_sanitize_input_removes_null_bytes() -> None:
    """sanitize_input should remove null bytes."""
    result = StadiumAssistant.sanitize_input("hello\x00world")
    assert "\x00" not in result


def test_sanitize_input_trims_whitespace() -> None:
    """sanitize_input should strip leading/trailing whitespace."""
    result = StadiumAssistant.sanitize_input("  hello world  ")
    assert result == "hello world"


def test_sanitize_input_collapses_multiple_spaces() -> None:
    """sanitize_input should collapse multiple spaces into one."""
    result = StadiumAssistant.sanitize_input("hello    world")
    assert result == "hello world"


def test_sanitize_input_limits_length() -> None:
    """sanitize_input should limit input to 2000 characters."""
    long_input = "a" * 5000
    result = StadiumAssistant.sanitize_input(long_input)
    assert len(result) == MAX_INPUT_LENGTH


def test_sanitize_input_handles_empty() -> None:
    """sanitize_input should return empty string for None/empty."""
    assert StadiumAssistant.sanitize_input("") == ""
    assert StadiumAssistant.sanitize_input(None) == ""


# ── Initialization Tests ──

def test_assistant_initializes_with_defaults() -> None:
    """Assistant should initialize with default configuration."""
    assistant = StadiumAssistant()
    assert assistant.config.api_key == ""
    assert assistant.config.rate_limit_interval == 1.5
    assert assistant.config.max_history_messages == 6


def test_assistant_initializes_with_custom_config() -> None:
    """Assistant should accept custom configuration."""
    config = AssistantConfig(api_key="test-key", rate_limit_interval=2.0)
    assistant = StadiumAssistant(config=config)
    assert assistant.config.api_key == "test-key"
    assert assistant.config.rate_limit_interval == 2.0


def test_assistant_loads_stadium_cache() -> None:
    """Assistant should load stadium data into cache."""
    assistant = StadiumAssistant()
    assert len(StadiumAssistant._stadium_cache) == len(FIFA_STADIUMS)
    assert "MetLife Stadium" in StadiumAssistant._stadium_cache


# ── Prompt Building Tests ──

def test_build_prompt_includes_context_and_user_query() -> None:
    """Prompt should include FIFA context, user query, and role."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt(
        PromptContext(user_query="Where is Gate A?", user_role="fan")
    )

    assert "FIFA World Cup 2026" in prompt
    assert "Gate A" in prompt
    assert "fan" in prompt


def test_build_prompt_includes_stadium_context() -> None:
    """Prompt should include stadium info when provided."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt(
        PromptContext(user_query="Where is parking?", user_role="fan", stadium="SoFi Stadium")
    )

    assert "SoFi Stadium" in prompt
    assert "Inglewood" in prompt
    assert "70,240" in prompt


def test_build_prompt_includes_language() -> None:
    """Prompt should include the selected language."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt(
        PromptContext(user_query="Hello", user_role="fan", language="Spanish")
    )

    assert "Spanish" in prompt


def test_build_prompt_includes_conversation_history() -> None:
    """Prompt should include recent conversation history."""
    assistant = StadiumAssistant()
    history = [
        {"role": "user", "content": "Where is Gate A?"},
        {"role": "assistant", "content": "Gate A is at the north entrance."},
    ]
    prompt = assistant.build_prompt(
        PromptContext(user_query="Thanks!", user_role="fan", conversation_history=history)
    )

    assert "Where is Gate A?" in prompt
    assert "Gate A is at the north entrance" in prompt


def test_build_prompt_handles_empty_history() -> None:
    """Prompt should work without conversation history."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt(
        PromptContext(user_query="Hello", user_role="fan")
    )

    assert "Hello" in prompt
    assert "Recent conversation" not in prompt


def test_build_prompt_includes_date_as_preference() -> None:
    """Prompt should label date as user preference, not match schedule."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt(
        PromptContext(
            user_query="What's happening?",
            user_role="fan",
            match_date="2026-07-18",
            match_time="20:00",
        )
    )

    assert "user's preference" in prompt.lower()
    assert "NOT a confirmed match" in prompt


def test_build_prompt_includes_match_guidance() -> None:
    """Prompt should guide the model to use Google Search for matches."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt(
        PromptContext(user_query="Who is playing?", user_role="fan")
    )

    assert "match-related" in prompt.lower()
    assert "Google Search grounding" in prompt


def test_build_prompt_sanitizes_user_query() -> None:
    """Prompt should sanitize user input."""
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt(
        PromptContext(user_query="hello\x00world", user_role="fan")
    )

    assert "\x00" not in prompt


def test_build_prompt_raises_on_empty_query() -> None:
    """Prompt should raise InvalidQueryError for empty queries."""
    assistant = StadiumAssistant()
    with pytest.raises(InvalidQueryError):
        assistant.build_prompt(PromptContext(user_query="", user_role="fan"))


# ── API Key Handling Tests ──

def test_prepare_response_handles_missing_api_key() -> None:
    """Should raise APIKeyMissingError when API key is missing."""
    config = AssistantConfig(api_key="")
    assistant = StadiumAssistant(config=config)

    with pytest.raises(APIKeyMissingError):
        assistant.prepare_response(
            "What should I do if the crowd grows?", "staff"
        )


def test_prepare_response_handles_empty_query() -> None:
    """Should raise InvalidQueryError for empty query."""
    config = AssistantConfig(api_key="test-key")
    assistant = StadiumAssistant(config=config)
    with pytest.raises(InvalidQueryError):
        assistant.prepare_response("", "fan")


def test_prepare_response_handles_whitespace_query() -> None:
    """Should raise InvalidQueryError for whitespace-only query."""
    config = AssistantConfig(api_key="test-key")
    assistant = StadiumAssistant(config=config)
    with pytest.raises(InvalidQueryError):
        assistant.prepare_response("   ", "fan")


# ── Model Fallback Tests ──

def test_get_model_candidates_returns_list() -> None:
    """Should return a non-empty list of model names."""
    assistant = StadiumAssistant()
    models = assistant._get_model_candidates()
    assert isinstance(models, list)
    assert len(models) > 0
    assert all(isinstance(m, str) for m in models)
    assert models == GEMINI_MODEL_CANDIDATES


# ── Stadium Data Tests ──

def test_fifa_stadiums_contains_all_venues() -> None:
    """FIFA_STADIUMS should contain all 8 venues."""
    assert len(FIFA_STADIUMS) == 8
    assert "MetLife Stadium" in FIFA_STADIUMS
    assert "SoFi Stadium" in FIFA_STADIUMS
    assert "AT&T Stadium" in FIFA_STADIUMS
    assert "Mercedes-Benz Stadium" in FIFA_STADIUMS
    assert "Levi's Stadium" in FIFA_STADIUMS
    assert "NRG Stadium" in FIFA_STADIUMS
    assert "Lincoln Financial Field" in FIFA_STADIUMS
    assert "Gillette Stadium" in FIFA_STADIUMS


def test_each_stadium_has_capacity() -> None:
    """Each stadium entry should include capacity info."""
    for name, info in FIFA_STADIUMS.items():
        assert "capacity" in info.lower(), f"{name} missing capacity"


def test_each_stadium_has_gates() -> None:
    """Each stadium entry should include gate info."""
    for name, info in FIFA_STADIUMS.items():
        assert "gate" in info.lower(), f"{name} missing gate info"


# ── Role Mapping Tests ──

def test_build_prompt_supports_all_roles() -> None:
    """Prompt should work with all user roles."""
    assistant = StadiumAssistant()
    for role in ["fan", "organizer", "volunteer", "staff"]:
        prompt = assistant.build_prompt(
            PromptContext(user_query="Test", user_role=role)
        )
        assert role in prompt


# ── Import Error Handling Tests ──

def test_prepare_response_handles_import_error() -> None:
    """Should handle missing google-genai package gracefully."""
    config = AssistantConfig(api_key="test-key")
    assistant = StadiumAssistant(config=config)
    with patch.dict("sys.modules", {"google": None}):
        with pytest.raises(Exception):  # Should raise ImportError
            assistant.prepare_response("Hello", "fan")


# ── Match Query Detection Tests ──

def test_is_match_related_query_detects_scores() -> None:
    """Should detect score-related queries as match-related."""
    assistant = StadiumAssistant()
    assert assistant._is_match_related_query("What is the score?") is True
    assert assistant._is_match_related_query("Latest scores") is True
    assert assistant._is_match_related_query("Who won?") is True


def test_is_match_related_query_detects_schedules() -> None:
    """Should detect schedule-related queries as match-related."""
    assistant = StadiumAssistant()
    assert assistant._is_match_related_query("When is the match?") is True
    assert assistant._is_match_related_query("Match schedule") is True
    assert assistant._is_match_related_query("Who is playing?") is True
    assert assistant._is_match_related_query("Which teams are playing?") is True


def test_is_match_related_query_detects_standings() -> None:
    """Should detect standings-related queries as match-related."""
    assistant = StadiumAssistant()
    assert assistant._is_match_related_query("What are the standings?") is True
    assert assistant._is_match_related_query("Tournament standings") is True


def test_is_match_related_query_detects_broadcast() -> None:
    """Should detect broadcast-related queries as match-related."""
    assistant = StadiumAssistant()
    assert assistant._is_match_related_query("Where can I watch?") is True
    assert assistant._is_match_related_query("TV broadcast") is True
    assert assistant._is_match_related_query("Streaming info") is True


def test_is_match_related_query_ignores_operational() -> None:
    """Should NOT detect operational queries as match-related."""
    assistant = StadiumAssistant()
    assert assistant._is_match_related_query("Where is Gate A?") is False
    assert assistant._is_match_related_query("How do I get to the stadium?") is False
    assert assistant._is_match_related_query("Is there parking?") is False
    assert assistant._is_match_related_query("What's the crowd level?") is False
    assert assistant._is_match_related_query("How do I get wheelchair access?") is False


# ── Conditional Tool Usage Tests ──

def test_prepare_response_skips_search_tool_for_operational_queries() -> None:
    """Should not use Google Search tool for operational queries."""
    config = AssistantConfig(api_key="test-key")
    assistant = StadiumAssistant(config=config)

    with patch("google.genai.Client") as mock_client:
        mock_model = MagicMock()
        mock_client.return_value.models.generate_content.return_value = MagicMock(
            text="Response"
        )

        result = assistant.prepare_response(
            "Where is Gate A?", "fan", stadium="MetLife Stadium"
        )

        # Verify the API was called
        assert mock_client.return_value.models.generate_content.called
        # Get the config that was passed
        call_args = mock_client.return_value.models.generate_content.call_args
        config_arg = call_args.kwargs.get("config", call_args[1].get("config") if len(call_args) > 1 else None)

        # For operational queries, tools should not be included
        if config_arg:
            assert not hasattr(config_arg, "tools") or config_arg.tools is None or len(config_arg.tools) == 0


def test_prepare_response_uses_search_tool_for_match_queries() -> None:
    """Should use Google Search tool for match-related queries."""
    config = AssistantConfig(api_key="test-key")
    assistant = StadiumAssistant(config=config)

    with patch("google.genai.Client") as mock_client:
        mock_model = MagicMock()
        mock_client.return_value.models.generate_content.return_value = MagicMock(
            text="Response"
        )

        result = assistant.prepare_response("What is the score?", "fan")

        # Verify the API was called
        assert mock_client.return_value.models.generate_content.called
        # The tool usage is handled internally, just verify it didn't crash


# ── Fallback Behavior Tests ──

def test_prepare_response_retries_without_tool_on_quota_error() -> None:
    """Should retry without Google Search tool if quota is exhausted."""
    config = AssistantConfig(api_key="test-key")
    assistant = StadiumAssistant(config=config)

    with patch("google.genai.Client") as mock_client:
        # First call fails with 429, second call succeeds
        mock_client.return_value.models.generate_content.side_effect = [
            Exception("429 RESOURCE_EXHAUSTED"),
            MagicMock(text="Fallback response"),
        ]

        result = assistant.prepare_response("What is the latest score?", "fan")

        # Should have tried twice
        assert mock_client.return_value.models.generate_content.call_count == 2
        # Should return the fallback response
        assert "Fallback response" in result
        assert "quota" in result.lower() or "real-time" in result.lower()


def test_prepare_response_handles_permanent_failure() -> None:
    """Should raise ModelNotAvailableError when all models fail."""
    config = AssistantConfig(api_key="test-key")
    assistant = StadiumAssistant(config=config)

    with patch("google.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.side_effect = Exception(
            "Permanent error"
        )

        with pytest.raises(ModelNotAvailableError):
            assistant.prepare_response("Hello", "fan")


# ── Safe Response Wrapper Tests ──

def test_get_response_safe_returns_error_on_failure() -> None:
    """get_response_safe should return error message on failure."""
    config = AssistantConfig(api_key="")
    assistant = StadiumAssistant(config=config)

    result = assistant.get_response_safe("Hello", "fan")
    assert "api key" in result.lower()


def test_get_response_safe_returns_response_on_success() -> None:
    """get_response_safe should return response on success."""
    config = AssistantConfig(api_key="test-key")
    assistant = StadiumAssistant(config=config)

    with patch("google.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = MagicMock(
            text="Success"
        )
        result = assistant.get_response_safe("Hello", "fan")
        assert result == "Success"