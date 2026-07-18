"""
Data classes for Stadium Intelligence Assistant.

Provides type-safe data structures for messages, configuration,
and API responses.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    """Represents a chat message in the conversation.

    Attributes:
        role: Message author - 'user' or 'assistant'.
        content: Message text content.
        timestamp: Optional timestamp for message ordering.
    """

    role: str
    content: str
    timestamp: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary format.

        Returns:
            Dictionary representation of the message.
        """
        result: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.timestamp is not None:
            result["timestamp"] = self.timestamp
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create Message from dictionary.

        Args:
            data: Dictionary with 'role' and 'content' keys.

        Returns:
            Message instance.
        """
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp"),
        )


@dataclass
class AssistantConfig:
    """Configuration for StadiumAssistant instance.

    Attributes:
        api_key: Gemini API key for authentication.
        rate_limit_interval: Minimum seconds between API calls.
        max_history_messages: Maximum conversation history to include.
        max_input_length: Maximum allowed input length.
    """

    api_key: str = ""
    rate_limit_interval: float = 1.5
    max_history_messages: int = 6
    max_input_length: int = 2000


@dataclass
class PromptContext:
    """Context information for building AI prompts.

    Attributes:
        user_query: The user's question.
        user_role: User role (fan, organizer, volunteer, staff).
        stadium: Selected stadium name.
        match_date: User's selected match date.
        match_time: User's selected match time.
        language: Response language.
        conversation_history: Previous chat messages.
    """

    user_query: str = ""
    user_role: str = "fan"
    stadium: str = ""
    match_date: str = ""
    match_time: str = ""
    language: str = "English"
    conversation_history: list[dict[str, str]] = field(default_factory=list)


@dataclass
class APIResponse:
    """Represents an API response from Gemini.

    Attributes:
        success: Whether the request succeeded.
        content: Response text content.
        error: Error message if request failed.
        model_used: Name of the model that generated the response.
        retry_count: Number of retry attempts made.
    """

    success: bool
    content: str = ""
    error: str | None = None
    model_used: str | None = None
    retry_count: int = 0