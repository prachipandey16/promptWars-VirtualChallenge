# Plan: Stadium Intelligence Assistant Enhanced UI

## Changes Required

### 1. UI Redesign — Football Aesthetic
- White background + green (#4CAF50) accent color
- Football ⚽ icon, pitch-green header
- ChatGPT-style chat interface
- Remove API key info from sidebar

### 2. Chat Interface (like ChatGPT)
- Scrollable chat history with user/AI message bubbles
- Input at bottom (sticky)
- Follow-up support: pass conversation history to Gemini
- Clear chat button

### 3. Stadium & Match Context
- Stadium selector dropdown (MetLife, SoFi, AT&T, Mercedes-Benz, etc.)
- Match date/time picker
- Language selector (English, Spanish, French)
- User role as icon-based radio buttons (not sidebar dropdown)

### 4. Smart Visual Responses
- Navigation → step-by-step with emoji arrows + landmarks
- Crowd info → color-coded indicators (🟢🟡🔴)
- Accessibility → wheelchair ♿ markers
- Transportation → shuttle/train options

### 5. Prompt Enhancement
- Include stadium, match time, language, conversation history
- Instruct model to use emojis and structured formatting

## Files to Modify
- `app.py` — complete rewrite for new UI
- `src/assistant.py` — enhanced prompt with context + history