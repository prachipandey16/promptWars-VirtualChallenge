"""
Constants and configuration for Stadium Intelligence Assistant.

Centralizes magic numbers, strings, and configuration values to improve
maintainability and reduce hardcoded values throughout the codebase.
"""

from typing import Final

# ── Input Validation Constants ──
MAX_INPUT_LENGTH: Final[int] = 2000
MAX_HISTORY_MESSAGES: Final[int] = 6  # Last 3 exchanges (user + assistant)

# ── Rate Limiting Constants ──
DEFAULT_RATE_LIMIT_INTERVAL: Final[float] = 2.0
ASSISTANT_RATE_LIMIT_INTERVAL: Final[float] = 1.5

# ── Model Configuration ──
GEMINI_MODEL_CANDIDATES: Final[list[str]] = [
    "gemini-3.1-flash-lite",  # Currently working model (as of test)
    "gemini-flash-latest",    # Fallback options
    "gemini-3.5-flash",
    "gemini-2.0-flash",
]

# ── Match Query Keywords ──
MATCH_KEYWORDS: Final[list[str]] = [
    "score", "scores", "result", "results", "playing", "played",
    "match", "game", "fixture", "schedule", "when is", "when are",
    "who is playing", "which teams", "standing", "standings",
    "winner", "won", "lost", "draw", "ticket", "tickets",
    "broadcast", "tv", "streaming", "watch", "live",
]

# ── Error Messages ──
ERROR_API_KEY_MISSING: Final[str] = (
    "⚠️ API key is missing. Set GEMINI_API_KEY in your .env file "
    "or Streamlit Cloud secrets before using the AI assistant."
)
ERROR_INVALID_QUERY: Final[str] = "⚠️ Please enter a valid question."
ERROR_EMPTY_RESPONSE: Final[str] = (
    "Unable to generate response with the available Gemini models. "
    "Last error: {error}"
)
ERROR_IMPORT_FAILED: Final[str] = (
    "⚠️ The google-genai package is not installed. "
    "Run: pip install google-genai"
)
ERROR_QUOTA_EXHAUSTED_NOTE: Final[str] = (
    "\n\n⚠️ Note: Real-time data unavailable due to API quota limits."
)

# ── Prompt Template Parts ──
PROMPT_SYSTEM_ROLE: Final[str] = (
    "You are the FIFA World Cup 2026 Stadium Intelligence Assistant. "
    "Respond in {language}. "
    "User role: {user_role}. "
)

PROMPT_STADIUM_CONTEXT: Final[str] = "Venue Info: {stadium} — {stadium_info}\n"
PROMPT_MATCH_CONTEXT: Final[str] = (
    "User's selected date/time: {match_date} at {match_time} "
    "(this is just the user's preference, NOT a confirmed match)\n"
)
PROMPT_MATCH_DATE_ONLY: Final[str] = (
    "User's selected date: {match_date} "
    "(this is just the user's preference, NOT a confirmed match)\n"
)

PROMPT_HISTORY_HEADER: Final[str] = "Recent conversation:\n"
PROMPT_HISTORY_SEPARATOR: Final[str] = "\n"
PROMPT_HISTORY_TRAILER: Final[str] = "\n\n"

PROMPT_GUIDELINES: Final[str] = (
    "Guidelines:\n"
    "- For navigation questions (routes, gates, directions): "
    "provide step-by-step directions with emoji arrows (→ ↑ ↓ ←) "
    "and mention landmarks\n"
    "- For crowd/traffic questions: use color indicators "
    "🟢(low) 🟡(moderate) 🔴(high)\n"
    "- For accessibility questions: highlight wheelchair-friendly "
    "routes ♿, ramps, elevators\n"
    "- For transportation questions: list options with estimated times\n"
    "- For general questions: answer clearly with relevant emojis\n"
    "- Be concise but helpful. Use bullet points for lists.\n"
    "- For match-related questions (teams playing, schedules, scores): "
    "use Google Search grounding to fetch the latest information "
    "and provide it to the user.\n"
    "- For operational questions (navigation, crowd, transport, "
    "accessibility): provide specific, actionable guidance.\n"
    "- If you genuinely don't know something, suggest the user check "
    "with stadium staff or official FIFA channels.\n\n"
)

# ── User Roles ──
USER_ROLES: Final[dict[str, str]] = {
    "😊 Fan": "fan",
    "📋 Organizer": "organizer",
    "🦺 Volunteer": "volunteer",
    "👔 Staff": "staff",
}

# ── Supported Languages ──
SUPPORTED_LANGUAGES: Final[list[str]] = [
    "English", "Spanish", "French", "German", "Portuguese", "Arabic"
]

# ── Stadium Venues ──
FIFA_STADIUMS: Final[dict[str, str]] = {
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

# ── UI Constants ──
PAGE_TITLE: Final[str] = "Stadium Assistant — FIFA World Cup 2026"
PAGE_ICON: Final[str] = "⚽"
PAGE_LAYOUT: Final[str] = "centered"

WELCOME_HEADER: Final[str] = "⚽ Stadium Intelligence Assistant"
WELCOME_SUBHEADER: Final[str] = (
    "FIFA World Cup 2026 — Your AI guide for stadiums, navigation, and match day"
)

SUGGESTED_QUESTIONS: Final[list[str]] = [
    "What's the best route to Gate A?",
    "How crowded will it be at halftime?",
    "Where is wheelchair access?",
]

# ── Sidebar Options ──
STADIUM_OPTIONS: Final[list[str]] = [
    "", "MetLife Stadium", "SoFi Stadium", "AT&T Stadium",
    "Mercedes-Benz Stadium", "Levi's Stadium", "NRG Stadium",
    "Lincoln Financial Field", "Gillette Stadium",
]

DEFAULT_MATCH_HOUR: Final[int] = 20
DEFAULT_MATCH_MINUTE: Final[int] = 0

# ── Chat Display ──
CHAT_ROLE_USER: Final[str] = "user"
CHAT_ROLE_ASSISTANT: Final[str] = "assistant"