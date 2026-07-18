"""
Custom exceptions for Stadium Intelligence Assistant.

Provides structured error handling with specific exception types
for different failure scenarios.
"""


class StadiumAssistantError(Exception):
    """Base exception for all Stadium Assistant errors."""

    def __init__(self, message: str, user_message: str | None = None) -> None:
        """Initialize with technical and user-friendly messages.

        Args:
            message: Technical error message for logging.
            user_message: User-friendly error message to display.
        """
        super().__init__(message)
        self.user_message = user_message or message


class APIKeyMissingError(StadiumAssistantError):
    """Raised when the Gemini API key is not configured."""

    def __init__(self) -> None:
        super().__init__(
            "GEMINI_API_KEY not found in environment or secrets",
            "⚠️ API key is missing. Set GEMINI_API_KEY in your .env file "
            "or Streamlit Cloud secrets before using the AI assistant.",
        )


class InvalidQueryError(StadiumAssistantError):
    """Raised when user input is invalid or empty."""

    def __init__(self, query: str) -> None:
        super().__init__(
            f"Invalid or empty query: {query[:50]}",
            "⚠️ Please enter a valid question.",
        )


class ModelNotAvailableError(StadiumAssistantError):
    """Raised when all Gemini models fail to respond."""

    def __init__(self, last_error: Exception) -> None:
        super().__init__(
            f"All Gemini models failed. Last error: {last_error}",
            "Unable to generate response with the available Gemini models. "
            "Please try again later.",
        )


class ImportError(StadiumAssistantError):
    """Raised when required packages are not installed."""

    def __init__(self) -> None:
        super().__init__(
            "google-genai package not installed",
            "⚠️ The google-genai package is not installed. "
            "Run: pip install google-genai",
        )


class RateLimitExceededError(StadiumAssistantError):
    """Raised when API rate limit is exceeded."""

    def __init__(self) -> None:
        super().__init__(
            "API rate limit exceeded",
            "⚠️ Too many requests. Please wait a moment and try again.",
        )