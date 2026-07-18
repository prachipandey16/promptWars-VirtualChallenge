"""
Stadium Intelligence Assistant — Core AI logic for FIFA World Cup 2026.

Provides stadium operations guidance using Google Gemini API with support for
multilingual queries, conversation history, role-based context, and structured
response formatting (navigation, crowd, accessibility, transportation).
"""

import logging
import os
import re
import time
from typing import Any

from src.constants import (
    ASSISTANT_RATE_LIMIT_INTERVAL,
    ERROR_EMPTY_RESPONSE,
    ERROR_QUOTA_EXHAUSTED_NOTE,
    FIFA_STADIUMS,
    GEMINI_MODEL_CANDIDATES,
    MAX_HISTORY_MESSAGES,
    MAX_INPUT_LENGTH,
    MATCH_KEYWORDS,
    PROMPT_GUIDELINES,
    PROMPT_HISTORY_HEADER,
    PROMPT_HISTORY_SEPARATOR,
    PROMPT_HISTORY_TRAILER,
    PROMPT_MATCH_CONTEXT,
    PROMPT_MATCH_DATE_ONLY,
    PROMPT_STADIUM_CONTEXT,
    PROMPT_SYSTEM_ROLE,
)
from src.dataclasses import AssistantConfig, Message, PromptContext
from src.exceptions import (
    APIKeyMissingError,
    ImportError,
    InvalidQueryError,
    ModelNotAvailableError,
    RateLimitExceededError,
    StadiumAssistantError,
)

# Configure module logger
logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter to prevent API quota exhaustion.

    Attributes:
        min_interval: Minimum seconds between API calls.
        last_call_time: Timestamp of the last API call.
    """

    def __init__(self, min_interval: float = ASSISTANT_RATE_LIMIT_INTERVAL) -> None:
        """Initialize the rate limiter.

        Args:
            min_interval: Minimum interval between calls in seconds.
        """
        self.min_interval: float = min_interval
        self.last_call_time: float = 0.0

    def wait_if_needed(self) -> None:
        """Sleep if called within min_interval seconds of last call.

        Raises:
            RateLimitExceededError: If rate limit is exceeded.
        """
        elapsed: float = time.time() - self.last_call_time
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
        self.last_call_time = time.time()


class StadiumAssistant:
    """AI assistant for FIFA World Cup 2026 stadium operations.

    Handles navigation, crowd management, accessibility, transportation,
    and general venue queries with role-based and multilingual support.

    Attributes:
        config: AssistantConfig instance with all settings.
        rate_limiter: RateLimiter instance to control API call frequency.
    """

    # Class-level cache for stadium data to avoid recomputation
    _stadium_cache: dict[str, str] = {}

    def __init__(self, config: AssistantConfig | None = None) -> None:
        """Initialize the assistant with configuration.

        Args:
            config: AssistantConfig instance. Uses defaults if not provided.
        """
        self.config: AssistantConfig = config or AssistantConfig()
        self.rate_limiter: RateLimiter = RateLimiter(
            min_interval=self.config.rate_limit_interval
        )

        # Populate stadium cache once
        if not self._stadium_cache:
            self._stadium_cache.update(FIFA_STADIUMS)
            logger.info(f"Loaded {len(self._stadium_cache)} stadiums into cache")

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input to prevent prompt injection.

        Args:
            text: Raw user input string.

        Returns:
            Sanitized string with special characters escaped and length limited.
        """
        if not text:
            return ""

        # Remove any null bytes
        text = text.replace("\x00", "")
        # Strip excessive whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Limit length to prevent abuse
        return text[:MAX_INPUT_LENGTH]

    def _build_stadium_context(self, stadium: str) -> str:
        """Build stadium context section of the prompt.

        Args:
            stadium: Selected stadium name.

        Returns:
            Formatted stadium context string.
        """
        if not stadium or stadium not in self._stadium_cache:
            return ""

        stadium_info = self._stadium_cache[stadium]
        logger.debug(f"Building context for stadium: {stadium}")
        return PROMPT_STADIUM_CONTEXT.format(
            stadium=stadium, stadium_info=stadium_info
        )

    def _build_match_context(self, match_date: str, match_time: str) -> str:
        """Build match context section of the prompt.

        Args:
            match_date: User's selected match date.
            match_time: User's selected match time.

        Returns:
            Formatted match context string.
        """
        if not match_date and not match_time:
            return ""

        if match_date and match_time:
            logger.debug(f"Building match context: {match_date} at {match_time}")
            return PROMPT_MATCH_CONTEXT.format(
                match_date=match_date, match_time=match_time
            )

        logger.debug(f"Building date-only context: {match_date}")
        return PROMPT_MATCH_DATE_ONLY.format(match_date=match_date)

    def _build_history_context(
        self, conversation_history: list[dict[str, str]]
    ) -> str:
        """Build conversation history section of the prompt.

        Args:
            conversation_history: Previous chat messages.

        Returns:
            Formatted history context string.
        """
        if not conversation_history:
            return ""

        # Use only the most recent messages
        recent_history = conversation_history[-MAX_HISTORY_MESSAGES:]
        history_lines: list[str] = []

        for msg in recent_history:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            safe_content = self.sanitize_input(msg.get("content", ""))
            history_lines.append(f"{role_label}: {safe_content}")

        if not history_lines:
            return ""

        logger.debug(f"Building history context with {len(history_lines)} messages")
        return (
            PROMPT_HISTORY_HEADER
            + PROMPT_HISTORY_SEPARATOR.join(history_lines)
            + PROMPT_HISTORY_TRAILER
        )

    def build_prompt(self, context: PromptContext) -> str:
        """Build a structured prompt for the Gemini API.

        Args:
            context: PromptContext with all necessary information.

        Returns:
            Formatted prompt string for the AI model.
        """
        # Sanitize the user query
        user_query = self.sanitize_input(context.user_query)
        if not user_query:
            raise InvalidQueryError(context.user_query)

        logger.debug(f"Building prompt for query: {user_query[:50]}...")

        # Build prompt sections
        stadium_context = self._build_stadium_context(context.stadium)
        match_context = self._build_match_context(context.match_date, context.match_time)
        history_context = self._build_history_context(context.conversation_history)

        # Assemble complete prompt
        prompt = (
            PROMPT_SYSTEM_ROLE.format(language=context.language, user_role=context.user_role)
            + stadium_context
            + match_context
            + history_context
            + PROMPT_GUIDELINES
            + f"User question: {user_query}"
        )

        logger.debug(f"Prompt built successfully ({len(prompt)} chars)")
        return prompt

    def _get_model_candidates(self) -> list[str]:
        """Return list of model names to try in order of preference.

        Returns:
            List of Gemini model name strings.
        """
        return GEMINI_MODEL_CANDIDATES.copy()

    def _is_match_related_query(self, user_query: str) -> bool:
        """Check if the query is about match information that needs web search.

        Args:
            user_query: The user's question.

        Returns:
            True if the query likely needs current match data from the web.
        """
        query_lower = user_query.lower()
        return any(keyword in query_lower for keyword in MATCH_KEYWORDS)

    def _call_gemini_api(
        self, prompt: str, use_search_tool: bool
    ) -> tuple[str, str | None]:
        """Call Gemini API with the given prompt.

        Args:
            prompt: Formatted prompt string.
            use_search_tool: Whether to enable Google Search tool.

        Returns:
            Tuple of (response_text, model_name) or (error_message, None).

        Raises:
            ModelNotAvailableError: If all models fail.
        """
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            logger.error("google-genai package not available")
            raise ImportError() from exc

        client = genai.Client(api_key=self.config.api_key)
        last_error: Exception | None = None

        # Configure tools if needed
        tools = None
        if use_search_tool:
            tools = [types.Tool(google_search=types.GoogleSearch())]

        # Try each model candidate
        for model_name in self._get_model_candidates():
            try:
                logger.debug(f"Trying model: {model_name}")

                # Build config - only include tools if needed
                config_kwargs: dict[str, Any] = {}
                if tools:
                    config_kwargs["tools"] = tools

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config_kwargs),
                )

                logger.info(f"Success with model: {model_name}")
                return response.text, model_name

            except Exception as exc:
                logger.warning(f"Model {model_name} failed: {exc}")

                # If Google Search tool caused quota exhaustion, retry without it
                if tools and "429" in str(exc):
                    logger.info("Quota exhausted, retrying without search tool")
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(),
                        )
                        return (
                            response.text + ERROR_QUOTA_EXHAUSTED_NOTE,
                            model_name,
                        )
                    except Exception as retry_exc:
                        logger.warning(f"Retry without tool failed: {retry_exc}")

                last_error = exc

        # All models failed
        error_msg = f"All models failed. Last error: {last_error}"
        logger.error(error_msg)
        raise ModelNotAvailableError(last_error or Exception("Unknown error"))

    def prepare_response(
        self,
        user_query: str,
        user_role: str = "fan",
        stadium: str = "",
        match_date: str = "",
        match_time: str = "",
        language: str = "English",
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        """Generate an AI response for the user's query.

        Args:
            user_query: The user's question.
            user_role: Role context (fan, organizer, volunteer, staff).
            stadium: Selected stadium name.
            match_date: User's selected match date.
            match_time: User's selected match time.
            language: Response language.
            conversation_history: Previous chat messages for context.

        Returns:
            AI-generated response string, or error message on failure.
        """
        # Validate API key
        if not self.config.api_key:
            logger.error("API key not configured")
            raise APIKeyMissingError()

        # Sanitize and validate input
        user_query = self.sanitize_input(user_query)
        if not user_query:
            logger.warning("Empty or invalid query received")
            raise InvalidQueryError(user_query)

        logger.info(f"Processing query: {user_query[:50]}...")

        # Apply rate limiting
        try:
            self.rate_limiter.wait_if_needed()
        except Exception as exc:
            logger.error(f"Rate limiter error: {exc}")
            raise RateLimitExceededError() from exc

        try:
            # Build prompt context
            context = PromptContext(
                user_query=user_query,
                user_role=user_role,
                stadium=stadium,
                match_date=match_date,
                match_time=match_time,
                language=language,
                conversation_history=conversation_history or [],
            )

            # Build prompt
            prompt = self.build_prompt(context)

            # Determine if we need Google Search tool
            use_search_tool = self._is_match_related_query(user_query)
            logger.debug(f"Match-related query: {use_search_tool}")

            # Call API
            response_text, model_name = self._call_gemini_api(prompt, use_search_tool)

            logger.info(f"Response generated successfully using {model_name}")
            return response_text

        except StadiumAssistantError:
            # Re-raise our custom exceptions
            raise
        except Exception as exc:
            logger.error(f"Unexpected error: {exc}", exc_info=True)
            raise ModelNotAvailableError(exc) from exc

    def get_response_safe(self, *args: Any, **kwargs: Any) -> str:
        """Safe wrapper for prepare_response that returns error messages.

        Args:
            *args: Positional arguments for prepare_response.
            **kwargs: Keyword arguments for prepare_response.

        Returns:
            Response string or error message.
        """
        try:
            return self.prepare_response(*args, **kwargs)
        except StadiumAssistantError as exc:
            logger.error(f"Assistant error: {exc}")
            return exc.user_message
        except Exception as exc:
            logger.error(f"Unexpected error in get_response_safe: {exc}")
            return f"Unable to generate response: {exc}"