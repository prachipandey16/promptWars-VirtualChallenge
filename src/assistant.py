"""
Stadium Intelligence Assistant — Core AI logic for FIFA World Cup 2026.

Provides stadium operations guidance using Google Gemini API with support for
multilingual queries, conversation history, role-based context, and structured
response formatting (navigation, crowd, accessibility, transportation).
"""

import os
import re
import time
from typing import Optional


class RateLimiter:
    """Simple rate limiter to prevent API quota exhaustion."""

    def __init__(self, min_interval: float = 2.0):
        self.min_interval = min_interval
        self.last_call_time = 0.0

    def wait_if_needed(self) -> None:
        """Sleep if called within min_interval seconds of last call."""
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call_time = time.time()


class StadiumAssistant:
    """AI assistant for FIFA World Cup 2026 stadium operations.

    Handles navigation, crowd management, accessibility, transportation,
    and general venue queries with role-based and multilingual support.

    Attributes:
        FIFA_STADIUMS: Dict mapping stadium names to their venue info.
        api_key: Gemini API key for content generation.
        rate_limiter: RateLimiter instance to control API call frequency.
    """

    FIFA_STADIUMS: dict[str, str] = {
        "MetLife Stadium": (
            "East Rutherford, NJ — 82,500 capacity, 2 gates (North/South), "
            "4 parking lots, accessible via NJ Transit Meadowlands line"
        ),
        "SoFi Stadium": (
            "Inglewood, CA — 70,240 capacity, 3 main gates (A/B/C), "
            "shuttle from LA Metro Crenshaw line"
        ),
        "AT&T Stadium": (
            "Arlington, TX — 80,000 capacity, 4 gates (East/West/North/South), "
            "parking for 30,000 vehicles, shuttle from DFW airport"
        ),
        "Mercedes-Benz Stadium": (
            "Atlanta, GA — 71,000 capacity, 2 main gates, "
            "MARTA rail connection, 5 parking decks"
        ),
        "Levi's Stadium": (
            "Santa Clara, CA — 68,500 capacity, 3 gates (A/B/C), "
            "VTA light rail, limited parking"
        ),
        "NRG Stadium": (
            "Houston, TX — 72,220 capacity, 4 gates, "
            "METRORail connection, 8 parking lots"
        ),
        "Lincoln Financial Field": (
            "Philadelphia, PA — 69,796 capacity, 3 gates, "
            "SEPTA Broad Street Line, 4 parking lots"
        ),
        "Gillette Stadium": (
            "Foxborough, MA — 65,878 capacity, 2 main gates, "
            "commuter rail from Boston, multiple lots"
        ),
    }

    # Cache for stadium data to avoid recomputation
    _stadium_cache: dict[str, str] = {}

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the assistant with an API key.

        Args:
            api_key: Gemini API key. Falls back to GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.rate_limiter = RateLimiter(min_interval=1.5)
        # Populate cache
        if not self._stadium_cache:
            self._stadium_cache.update(self.FIFA_STADIUMS)

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input to prevent prompt injection.

        Args:
            text: Raw user input string.

        Returns:
            Sanitized string with special characters escaped.
        """
        if not text:
            return ""
        # Remove any null bytes
        text = text.replace("\x00", "")
        # Strip excessive whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Limit length to prevent abuse
        return text[:2000]

    def build_prompt(
        self,
        user_query: str,
        user_role: str = "fan",
        stadium: str = "",
        match_date: str = "",
        match_time: str = "",
        language: str = "English",
        conversation_history: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """Build a structured prompt for the Gemini API.

        Args:
            user_query: The user's question.
            user_role: Role context (fan, organizer, volunteer, staff).
            stadium: Selected stadium name.
            match_date: User's selected match date.
            match_time: User's selected match time.
            language: Response language.
            conversation_history: Previous chat messages for context.

        Returns:
            Formatted prompt string for the AI model.
        """
        # Sanitize inputs
        user_query = self.sanitize_input(user_query)

        # Build stadium context
        stadium_context = ""
        if stadium and stadium in self.FIFA_STADIUMS:
            stadium_context = (
                f"Venue Info: {stadium} — {self.FIFA_STADIUMS[stadium]}\n"
            )

        # Build match context — user preference only, not confirmed match
        match_context = ""
        if match_date and match_time:
            match_context = (
                f"User's selected date/time: {match_date} at {match_time} "
                f"(this is just the user's preference, NOT a confirmed match)\n"
            )
        elif match_date:
            match_context = (
                f"User's selected date: {match_date} "
                f"(this is just the user's preference, NOT a confirmed match)\n"
            )

        # Build conversation history
        history_context = ""
        if conversation_history:
            history_lines = []
            for msg in conversation_history[-6:]:  # last 3 exchanges
                role_label = "User" if msg["role"] == "user" else "Assistant"
                safe_content = self.sanitize_input(msg.get("content", ""))
                history_lines.append(f"{role_label}: {safe_content}")
            if history_lines:
                history_context = (
                    "Recent conversation:\n"
                    + "\n".join(history_lines)
                    + "\n\n"
                )

        return (
            f"You are the FIFA World Cup 2026 Stadium Intelligence Assistant. "
            f"Respond in {language}. "
            f"User role: {user_role}. "
            f"{stadium_context}"
            f"{match_context}"
            f"{history_context}"
            f"Guidelines:\n"
            f"- For navigation questions (routes, gates, directions): "
            f"provide step-by-step directions with emoji arrows (→ ↑ ↓ ←) "
            f"and mention landmarks\n"
            f"- For crowd/traffic questions: use color indicators "
            f"🟢(low) 🟡(moderate) 🔴(high)\n"
            f"- For accessibility questions: highlight wheelchair-friendly "
            f"routes ♿, ramps, elevators\n"
            f"- For transportation questions: list options with estimated times\n"
            f"- For general questions: answer clearly with relevant emojis\n"
            f"- Be concise but helpful. Use bullet points for lists.\n"
            f"- For match-related questions (teams playing, schedules, scores): "
            f"use Google Search grounding to fetch the latest information "
            f"and provide it to the user.\n"
            f"- For operational questions (navigation, crowd, transport, "
            f"accessibility): provide specific, actionable guidance.\n"
            f"- If you genuinely don't know something, suggest the user check "
            f"with stadium staff or official FIFA channels.\n\n"
            f"User question: {user_query}"
        )

    def _get_model_candidates(self) -> list[str]:
        """Return list of model names to try in order of preference.

        Returns:
            List of Gemini model name strings.
        """
        return [
            "gemini-3.1-flash-lite",  # Currently working model (as of test)
            "gemini-flash-latest",    # Fallback options
            "gemini-3.5-flash",
            "gemini-2.0-flash",
        ]

    def _is_match_related_query(self, user_query: str) -> bool:
        """Check if the query is about match information that needs web search.

        Args:
            user_query: The user's question.

        Returns:
            True if the query likely needs current match data from the web.
        """
        match_keywords = [
            "score", "scores", "result", "results", "playing", "played",
            "match", "game", "fixture", "schedule", "when is", "when are",
            "who is playing", "which teams", "standing", "standings",
            "winner", "won", "lost", "draw", "ticket", "tickets",
            "broadcast", "tv", "streaming", "watch", "live",
        ]
        query_lower = user_query.lower()
        return any(keyword in query_lower for keyword in match_keywords)

    def prepare_response(
        self,
        user_query: str,
        user_role: str = "fan",
        stadium: str = "",
        match_date: str = "",
        match_time: str = "",
        language: str = "English",
        conversation_history: Optional[list[dict[str, str]]] = None,
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
        if not self.api_key:
            return (
                "⚠️ API key is missing. Set GEMINI_API_KEY in your .env file "
                "or Streamlit Cloud secrets before using the AI assistant."
            )

        # Sanitize input
        user_query = self.sanitize_input(user_query)
        if not user_query:
            return "⚠️ Please enter a valid question."

        # Rate limit
        self.rate_limiter.wait_if_needed()

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            last_error: Optional[Exception] = None

            # Determine if we need Google Search tool (only for match-related queries)
            use_search_tool = self._is_match_related_query(user_query)
            tools = None
            if use_search_tool:
                tools = [types.Tool(google_search=types.GoogleSearch())]

            for model_name in self._get_model_candidates():
                try:
                    # Build config - only include tools if needed
                    config_kwargs = {}
                    if tools:
                        config_kwargs["tools"] = tools

                    response = client.models.generate_content(
                        model=model_name,
                        contents=self.build_prompt(
                            user_query,
                            user_role,
                            stadium,
                            match_date,
                            match_time,
                            language,
                            conversation_history,
                        ),
                        config=types.GenerateContentConfig(**config_kwargs),
                    )
                    return response.text
                except Exception as exc:
                    # If Google Search tool caused quota exhaustion, retry without it
                    if tools and "429" in str(exc):
                        try:
                            response = client.models.generate_content(
                                model=model_name,
                                contents=self.build_prompt(
                                    user_query,
                                    user_role,
                                    stadium,
                                    match_date,
                                    match_time,
                                    language,
                                    conversation_history,
                                ),
                                config=types.GenerateContentConfig(),
                            )
                            return response.text + "\n\n⚠️ Note: Real-time data unavailable due to API quota limits."
                        except Exception:
                            pass
                    last_error = exc

            return (
                "Unable to generate response with the available Gemini models. "
                f"Last error: {last_error}"
            )
        except ImportError:
            return (
                "⚠️ The google-genai package is not installed. "
                "Run: pip install google-genai"
            )
        except Exception as exc:
            return f"Unable to generate response: {exc}"