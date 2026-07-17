# Stadium Intelligence Assistant

A GenAI-enabled Streamlit app for FIFA World Cup 2026 stadium operations support.

## Features
- Natural language assistance for fans, organizers, volunteers, and staff
- Gemini API integration for fast and relevant guidance
- Clean and accessible UI for deployment in Streamlit

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a .env file or export your key:
   ```bash
   GEMINI_API_KEY=your_key_here
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Testing
```bash
python -m pytest -q
```