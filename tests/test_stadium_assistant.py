import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.assistant import StadiumAssistant


def test_build_prompt_includes_context_and_user_query():
    assistant = StadiumAssistant()
    prompt = assistant.build_prompt("Where is Gate A?", "fan")

    assert "FIFA World Cup 2026" in prompt
    assert "Gate A" in prompt
    assert "fan" in prompt


def test_prepare_response_handles_missing_api_key():
    assistant = StadiumAssistant()

    with patch.dict(os.environ, {}, clear=True):
        result = assistant.prepare_response("What should I do if the crowd grows?", "staff")

    assert "api key" in result.lower()
