"""
Stadium Intelligence Assistant — Streamlit UI for FIFA World Cup 2026.

Provides an accessible, ChatGPT-style chat interface with football aesthetic,
stadium context selection, multilingual support, and role-based assistance.
"""

import os
from datetime import datetime, date
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

from src.assistant import StadiumAssistant
from src.constants import (
    CHAT_ROLE_ASSISTANT,
    CHAT_ROLE_USER,
    DEFAULT_MATCH_HOUR,
    DEFAULT_MATCH_MINUTE,
    ERROR_API_KEY_MISSING,
    FIFA_STADIUMS,
    PAGE_ICON,
    PAGE_LAYOUT,
    PAGE_TITLE,
    STADIUM_OPTIONS,
    SUPPORTED_LANGUAGES,
    USER_ROLES,
    WELCOME_HEADER,
    WELCOME_SUBHEADER,
)

# ── Custom CSS: Football Aesthetic + Accessibility ──
CUSTOM_CSS: str = """
<style>
    /* ── CSS Variables for Theming ── */
    :root {
        --primary: #2c2c2c;
        --primary-dark: #000000;
        --primary-light: #f5f5f5;
        --bg: #ffffff;
        --text: #1a1a1a;
        --text-secondary: #404040;
        --text-muted: #757575;
        --bubble-user-bg: #e8e8e8;
        --bubble-user-text: #1a1a1a;
        --bubble-ai-bg: #f8f8f8;
        --bubble-ai-text: #1a1a1a;
        --border: #d0d0d0;
        --focus-ring: #404040;
        --accent: #333333;
    }

    /* High contrast mode */
    .high-contrast {
        --primary: #000000;
        --primary-dark: #000000;
        --primary-light: #ffffff;
        --bg: #ffffff;
        --text: #000000;
        --text-secondary: #000000;
        --text-muted: #000000;
        --bubble-user-bg: #e0e0e0;
        --bubble-user-text: #000000;
        --bubble-ai-bg: #ffffff;
        --bubble-ai-text: #000000;
        --border: #000000;
        --focus-ring: #000000;
        --accent: #000000;
    }

    /* Main background */
    .stApp {
        background-color: var(--bg);
        color: var(--text);
    }

    /* Header styling - Black and white football theme */
    .header {
        background: linear-gradient(135deg, #1a1a1a 0%, #333333 100%);
        padding: 1.5rem 2rem;
        border-radius: 0 0 20px 20px;
        margin-bottom: 1.5rem;
        text-align: center;
        color: white;
        border-bottom: 3px solid #000000;
    }
    .header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.95;
        font-size: 0.9rem;
        color: #f0f0f0;
    }

    /* Chat container */
    .chat-container {
        max-width: 700px;
        margin: 0 auto;
        padding: 0 0.5rem;
    }

    /* Chat log for screen readers */
    .chat-log {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }

    /* Message bubbles */
    .user-bubble {
        background-color: var(--bubble-user-bg);
        color: var(--bubble-user-text);
        padding: 0.8rem 1rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0;
        max-width: 85%;
        margin-left: auto;
        font-size: 0.95rem;
        line-height: 1.4;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        word-wrap: break-word;
    }
    .assistant-bubble {
        background-color: var(--bubble-ai-bg);
        color: var(--bubble-ai-text);
        padding: 0.8rem 1rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        max-width: 85%;
        margin-right: auto;
        font-size: 0.95rem;
        line-height: 1.4;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        word-wrap: break-word;
    }

    /* Input area */
    .input-area {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--bg);
        padding: 1rem 1rem 1.5rem;
        border-top: 1px solid var(--border);
        z-index: 100;
    }
    .input-area .stTextInput > div > div > input {
        border-radius: 25px !important;
        border: 2px solid var(--primary) !important;
        padding: 0.6rem 1.2rem !important;
        font-size: 0.95rem !important;
        color: var(--text) !important;
        background: var(--bg) !important;
    }
    .input-area .stTextInput > div > div > input:focus {
        border-color: var(--focus-ring) !important;
        box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.3) !important;
        outline: none !important;
    }

    /* Sidebar styling */
    .sidebar-section {
        padding: 0.5rem 0;
    }
    .sidebar-section h3 {
        color: var(--primary-dark);
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        border-bottom: 2px solid var(--primary);
        padding-bottom: 0.3rem;
    }

    /* Focus indicators for keyboard navigation */
    button:focus-visible,
    input:focus-visible,
    select:focus-visible {
        outline: 3px solid var(--focus-ring) !important;
        outline-offset: 2px !important;
    }

    /* Scrollable chat */
    .chat-scroll {
        padding-bottom: 120px;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Spinner color */
    .stSpinner > div > div {
        border-color: var(--primary) !important;
    }

    /* Football-themed decorative elements */
    .header::before {
        content: "⚽";
        position: absolute;
        font-size: 4rem;
        opacity: 0.1;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 0;
    }
    .header h1, .header p {
        position: relative;
        z-index: 1;
    }

    /* Subtle football pattern for sidebar */
    .stSidebar {
        background-image: repeating-linear-gradient(
            45deg,
            transparent,
            transparent 10px,
            rgba(0, 0, 0, 0.02) 10px,
            rgba(0, 0, 0, 0.02) 20px
        );
    }

    /* Button styling - black and white theme */
    .stButton > button {
        background-color: #2c2c2c;
        color: white;
        border: 2px solid #000000;
        border-radius: 10px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #000000;
        border-color: #000000;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    /* Skip to content link for screen readers */
    .skip-link {
        position: absolute;
        top: -40px;
        left: 0;
        background: var(--primary-dark);
        color: white;
        padding: 8px;
        z-index: 1000;
        transition: top 0.2s;
    }
    .skip-link:focus {
        top: 0;
    }
}
</style>
"""

# Load API key: Streamlit Cloud secrets first, then .env for local dev
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
try:
    GEMINI_API_KEY: Optional[str] = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
except Exception:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ── Helper Functions ──
def _render_sidebar_section(title: str, aria_label: str) -> None:
    """Render a sidebar section with proper accessibility attributes.
    
    Args:
        title: Section title with emoji.
        aria_label: ARIA label for the section.
    """
    st.markdown(
        f"<div class='sidebar-section' role='region' aria-label='{aria_label}'>"
        f"<h3>{title}</h3></div>",
        unsafe_allow_html=True,
    )


def _render_welcome_message() -> None:
    """Render the welcome message with suggested questions."""
    st.markdown(
        """
        <div style="text-align: center; padding: 3rem 1rem; color: var(--text-muted);"
             role="status" aria-label="Welcome message">
            <div style="font-size: 3rem; margin-bottom: 1rem;" aria-hidden="true">⚽</div>
            <h2 style="font-size: 1.1rem; font-weight: 500; color: var(--text-secondary); margin: 0.5rem 0;">
                Ask me anything about FIFA World Cup 2026 stadiums!
            </h2>
            <p style="font-size: 0.85rem; margin-top: 0.5rem; color: var(--text-muted);">
                <strong>Try asking:</strong>
            </p>
            <ul style="font-size: 0.85rem; color: var(--text-muted); list-style: none; padding: 0;">
                <li>"What's the best route to Gate A?"</li>
                <li>"How crowded will it be at halftime?"</li>
                <li>"Where is wheelchair access?"</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_chat_message(msg: dict[str, str]) -> None:
    """Render a single chat message bubble.
    
    Args:
        msg: Message dictionary with 'role' and 'content' keys.
    """
    role_label: str = "You said" if msg["role"] == CHAT_ROLE_USER else "Assistant replied"
    bubble_class: str = "user-bubble" if msg["role"] == CHAT_ROLE_USER else "assistant-bubble"
    content_preview: str = msg["content"][:100] if len(msg["content"]) > 100 else msg["content"]
    
    st.markdown(
        f'<div class="{bubble_class}" role="article" '
        f'aria-label="{role_label}: {content_preview}">'
        f'{msg["content"]}</div>',
        unsafe_allow_html=True,
    )


# ── Page Config ──
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=PAGE_LAYOUT,
)

# ── Custom CSS: Football Aesthetic + Accessibility ──
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Skip Navigation Link (Accessibility) ──
st.markdown(
    '<a href="#chat-content" class="skip-link">Skip to chat content</a>',
    unsafe_allow_html=True,
)

# ── Header ──
st.markdown(
    f"""
    <div class="header" role="banner">
        <h1>{WELCOME_HEADER}</h1>
        <p>{WELCOME_SUBHEADER}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar: Stadium & Match Context ──
with st.sidebar:
    _render_sidebar_section("🏟️ Stadium", "Stadium selection")
    stadium = st.selectbox(
        "Select venue",
        STADIUM_OPTIONS,
        key="stadium",
        label_visibility="collapsed",
        help="Select the stadium venue you want to ask about",
    )

    _render_sidebar_section("📅 Match Day", "Match day and time")
    col1, col2 = st.columns(2)
    with col1:
        match_date = st.date_input(
            "Date",
            date.today(),
            key="match_date",
            label_visibility="collapsed",
        )
    with col2:
        default_time = datetime.now().time().replace(
            hour=DEFAULT_MATCH_HOUR, minute=DEFAULT_MATCH_MINUTE
        )
        match_time = st.time_input(
            "Time",
            default_time,
            key="match_time",
            label_visibility="collapsed",
        )

    _render_sidebar_section("🌐 Language", "Language selection")
    language = st.selectbox(
        "Language",
        SUPPORTED_LANGUAGES,
        key="language",
        label_visibility="collapsed",
    )

    _render_sidebar_section("👤 Your Role", "User role selection")
    role_display = st.radio(
        "Role",
        list(USER_ROLES.keys()),
        key="role",
        label_visibility="collapsed",
        index=0,
    )
    user_role: str = USER_ROLES[role_display]

    # Accessibility: High contrast toggle
    st.markdown("---")
    _render_sidebar_section("♿ Accessibility", "Accessibility settings")
    high_contrast = st.checkbox("High Contrast Mode", key="high_contrast")
    
    st.markdown("<br>", unsafe_allow_html=True)
    _render_sidebar_section("⌨️ Keyboard Shortcuts", "Keyboard shortcuts")
    st.markdown(
        "<small>"
        "• <kbd>Enter</kbd> to send message<br>"
        "• <kbd>Tab</kbd> to navigate<br>"
        "• <kbd>Esc</kbd> to clear input"
        "</small>",
        unsafe_allow_html=True,
    )

# Apply high contrast mode
if high_contrast:
    st.markdown(
        '<script>document.body.classList.add("high-contrast");</script>',
        unsafe_allow_html=True,
    )

# ── Initialize session state ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "assistant" not in st.session_state:
    from src.dataclasses import AssistantConfig
    from src.assistant import StadiumAssistant
    config = AssistantConfig(api_key=GEMINI_API_KEY)
    st.session_state.assistant = StadiumAssistant(config)

# ── API Key Warning ──
if not GEMINI_API_KEY:
    st.warning(
        ERROR_API_KEY_MISSING,
        icon="⚠️",
    )

# ── Chat Display ──
st.markdown(
    '<div class="chat-scroll" id="chat-content" role="log" '
    'aria-label="Chat conversation" aria-live="polite" aria-atomic="false">',
    unsafe_allow_html=True,
)

# Screen reader announcements for dynamic content
st.markdown(
    '<div id="sr-announcements" class="chat-log" aria-live="assertive" aria-atomic="true"></div>',
    unsafe_allow_html=True,
)

# Show welcome message if no messages
if not st.session_state.messages:
    _render_welcome_message()

# Display chat messages
for msg in st.session_state.messages:
    _render_chat_message(msg)

st.markdown('</div>', unsafe_allow_html=True)

# ── Input Area (fixed at bottom) ──
st.markdown(
    '<div class="input-area" role="region" aria-label="Message input">',
    unsafe_allow_html=True,
)


def handle_submit() -> None:
    """Process user input, get AI response, and update chat."""
    user_msg: str = st.session_state.user_input.strip()
    if not user_msg:
        return

    # Add user message
    st.session_state.messages.append({
        "role": CHAT_ROLE_USER,
        "content": user_msg,
    })

    # Get AI response
    with st.spinner("Thinking..."):
        response: str = st.session_state.assistant.prepare_response(
            user_query=user_msg,
            user_role=user_role,
            stadium=stadium,
            match_date=str(match_date) if match_date else "",
            match_time=str(match_time) if match_time else "",
            language=language,
            conversation_history=st.session_state.messages[:-1],
        )

    # Add assistant response
    st.session_state.messages.append({
        "role": CHAT_ROLE_ASSISTANT,
        "content": response,
    })


with st.form(key="chat_form", clear_on_submit=True):
    cols = st.columns([6, 1])
    with cols[0]:
        st.text_input(
            "Message input",
            placeholder="Ask about stadiums, routes, crowds, or match day...",
            key="user_input",
            label_visibility="collapsed",
            help="Enter your question about stadiums, navigation, or match day",
        )
    with cols[1]:
        submitted = st.form_submit_button(
            "➤ Send",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        handle_submit()
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ── Clear Chat Button (in sidebar) ──
with st.sidebar:
    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ── Main Execution Guard ──
if __name__ == "__main__":
    pass  # Streamlit apps run automatically
