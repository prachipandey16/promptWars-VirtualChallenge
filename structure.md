# Project Structure and Plan

## Problem Statement
Build a GenAI-enabled solution that enhances stadium operations and the overall tournament experience for fans, organizers, volunteers, or venue staff during the FIFA World Cup 2026. The solution must use Generative AI to improve navigation, crowd management, accessibility, transportation, sustainability, multilingual assistance, operational intelligence, or real-time decision support.

## Proposed Solution
Create a clean and accessible Streamlit web app called Stadium Intelligence Assistant. It helps users ask natural-language questions about stadium operations and receive AI-generated guidance based on the FIFA World Cup 2026 context.

## Core Features
- Natural language query interface for fans and staff
- Gemini API-based answer generation
- Role-based context handling for fan, organizer, volunteer, and staff
- Clean sidebar configuration for API key and role selection
- Simple error handling for missing API keys

## Architecture
- Frontend: Streamlit UI
- Backend: Python service layer with a dedicated assistant class
- AI provider: Google Gemini API
- Configuration: environment variables and .env support
- Testing: pytest for prompt construction and fallback behavior

## File Structure
- app.py: main Streamlit application entry point
- src/assistant.py: assistant logic and Gemini integration
- tests/test_stadium_assistant.py: core tests
- requirements.txt: Python dependencies

## Security Considerations
- API key is read from environment variables or .env
- Secrets are not hardcoded into source files
- Error messages do not expose sensitive data

## Efficiency Considerations
- Lightweight model selection for fast responses
- Minimal dependencies and low-latency request flow

## Accessibility Considerations
- High-contrast layout
- Clear labels and text prompts
- Simple keyboard-friendly Streamlit controls

## Testing Plan
- Unit tests for prompt building
- Unit tests for missing API key handling
- Manual UI validation in Streamlit

## Deployment Notes
- Deploy on Streamlit Cloud or similar hosting
- Set GEMINI_API_KEY as a secret environment variable
