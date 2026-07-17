import os
from typing import Optional


class StadiumAssistant:
    FIFA_STADIUMS = {
        "MetLife Stadium": "East Rutherford, NJ — 82,500 capacity, 2 gates (North/South), 4 parking lots, accessible via NJ Transit Meadowlands line",
        "SoFi Stadium": "Inglewood, CA — 70,240 capacity, 3 main gates (A/B/C), shuttle from LA Metro Crenshaw line",
        "AT&T Stadium": "Arlington, TX — 80,000 capacity, 4 gates (East/West/North/South), parking for 30,000 vehicles, shuttle from DFW airport",
        "Mercedes-Benz Stadium": "Atlanta, GA — 71,000 capacity, 2 main gates, MARTA rail connection, 5 parking decks",
        "Levi's Stadium": "Santa Clara, CA — 68,500 capacity, 3 gates (A/B/C), VTA light rail, limited parking",
        "NRG Stadium": "Houston, TX — 72,220 capacity, 4 gates, METRORail connection, 8 parking lots",
        "Lincoln Financial Field": "Philadelphia, PA — 69,796 capacity, 3 gates, SEPTA Broad Street Line, 4 parking lots",
        "Gillette Stadium": "Foxborough, MA — 65,878 capacity, 2 main gates, commuter rail from Boston, multiple lots",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def build_prompt(
        self,
        user_query: str,
        user_role: str = "fan",
        stadium: str = "",
        match_date: str = "",
        match_time: str = "",
        language: str = "English",
        conversation_history: Optional[list] = None,
    ) -> str:
        # Build stadium context
        stadium_context = ""
        if stadium and stadium in self.FIFA_STADIUMS:
            stadium_context = f"Venue Info: {stadium} — {self.FIFA_STADIUMS[stadium]}\n"

        # Build match context — only include date/time as user preference, NOT as match schedule
        match_context = ""
        if match_date and match_time:
            match_context = f"User's selected date/time: {match_date} at {match_time} (this is just the user's preference, NOT a confirmed match)\n"
        elif match_date:
            match_context = f"User's selected date: {match_date} (this is just the user's preference, NOT a confirmed match)\n"

        # Build conversation history
        history_context = ""
        if conversation_history:
            history_lines = []
            for msg in conversation_history[-6:]:  # last 3 exchanges
                role = "User" if msg["role"] == "user" else "Assistant"
                history_lines.append(f"{role}: {msg['content']}")
            if history_lines:
                history_context = "Recent conversation:\n" + "\n".join(history_lines) + "\n\n"

        return (
            f"You are the FIFA World Cup 2026 Stadium Intelligence Assistant. "
            f"Respond in {language}. "
            f"User role: {user_role}. "
            f"{stadium_context}"
            f"{match_context}"
            f"{history_context}"
            f"Guidelines:\n"
            f"- For navigation questions (routes, gates, directions): provide step-by-step directions with emoji arrows (→ ↑ ↓ ←) and mention landmarks\n"
            f"- For crowd/traffic questions: use color indicators 🟢(low) 🟡(moderate) 🔴(high)\n"
            f"- For accessibility questions: highlight wheelchair-friendly routes ♿, ramps, elevators\n"
            f"- For transportation questions: list options with estimated times\n"
            f"- For general questions: answer clearly with relevant emojis\n"
            f"- Be concise but helpful. Use bullet points for lists.\n"
            f"- IMPORTANT: You do NOT have access to real-time match schedules, team fixtures, or scores. If asked about which teams are playing, specific match details, or scores, state honestly that you don't have that information and suggest checking the official FIFA website or stadium screens.\n"
            f"- Do NOT invent or hallucinate match fixtures, teams, or schedules.\n"
            f"- If you don't know, suggest the user contact stadium staff or check official FIFA channels.\n\n"
            f"User question: {user_query}"
        )

    def _get_model_candidates(self) -> list[str]:
        return [
            "gemini-3.1-flash-lite",
        ]

    def prepare_response(
        self,
        user_query: str,
        user_role: str = "fan",
        stadium: str = "",
        match_date: str = "",
        match_time: str = "",
        language: str = "English",
        conversation_history: Optional[list] = None,
    ) -> str:
        if not self.api_key:
            return (
                "⚠️ API key is missing. Set GEMINI_API_KEY in your .env file "
                "before using the AI assistant."
            )

        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)
            last_error = None

            for model_name in self._get_model_candidates():
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
                    )
                    return response.text
                except Exception as exc:
                    last_error = exc

            return (
                "Unable to generate response with the available Gemini models. "
                f"Last error: {last_error}"
            )
        except Exception as exc:
            return f"Unable to generate response: {exc}"