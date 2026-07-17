import os
from datetime import datetime, date
from dotenv import load_dotenv
import streamlit as st
from src.assistant import StadiumAssistant

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ── Page Config ──
st.set_page_config(page_title="Stadium Assistant", page_icon="⚽", layout="centered")

# ── Custom CSS: Football Aesthetic ──
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Header styling */
    .header {
        background: linear-gradient(135deg, #1B5E20, #4CAF50);
        padding: 1.5rem 2rem;
        border-radius: 0 0 20px 20px;
        margin-bottom: 1.5rem;
        text-align: center;
        color: white;
    }
    .header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.9;
        font-size: 0.9rem;
    }
    
    /* Chat container */
    .chat-container {
        max-width: 700px;
        margin: 0 auto;
        padding: 0 0.5rem;
    }
    
    /* Message bubbles */
    .user-bubble {
        background-color: #E8F5E9;
        color: #1B5E20;
        padding: 0.8rem 1rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0;
        max-width: 85%;
        margin-left: auto;
        font-size: 0.95rem;
        line-height: 1.4;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .assistant-bubble {
        background-color: #F5F5F5;
        color: #212121;
        padding: 0.8rem 1rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        max-width: 85%;
        margin-right: auto;
        font-size: 0.95rem;
        line-height: 1.4;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Input area */
    .input-area {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 1rem 1rem 1.5rem;
        border-top: 1px solid #E0E0E0;
        z-index: 100;
    }
    .input-area .stTextInput > div > div > input {
        border-radius: 25px !important;
        border: 2px solid #4CAF50 !important;
        padding: 0.6rem 1.2rem !important;
        font-size: 0.95rem !important;
    }
    .input-area .stTextInput > div > div > input:focus {
        border-color: #1B5E20 !important;
        box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
    }
    
    /* Sidebar styling */
    .sidebar-section {
        padding: 0.5rem 0;
    }
    .sidebar-section h3 {
        color: #1B5E20;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        border-bottom: 2px solid #4CAF50;
        padding-bottom: 0.3rem;
    }
    
    /* Role selector */
    .role-btn {
        display: inline-block;
        padding: 0.3rem 0.7rem;
        margin: 0.2rem;
        border-radius: 20px;
        font-size: 0.8rem;
        cursor: pointer;
        border: 2px solid #E0E0E0;
        background: white;
        transition: all 0.2s;
    }
    .role-btn.active {
        border-color: #4CAF50;
        background: #E8F5E9;
        color: #1B5E20;
    }
    
    /* Clear button */
    .clear-btn {
        color: #757575;
        font-size: 0.8rem;
        text-align: center;
        cursor: pointer;
        padding: 0.5rem;
    }
    .clear-btn:hover {
        color: #D32F2F;
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
        border-color: #4CAF50 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown("""
<div class="header">
    <h1>⚽ Stadium Intelligence Assistant</h1>
    <p>FIFA World Cup 2026 — Your AI guide for stadiums, navigation, and match day</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar: Stadium & Match Context ──
with st.sidebar:
    st.markdown("<div class='sidebar-section'><h3>🏟️ Stadium</h3></div>", unsafe_allow_html=True)
    stadium = st.selectbox(
        "Select venue",
        ["", "MetLife Stadium", "SoFi Stadium", "AT&T Stadium", "Mercedes-Benz Stadium",
         "Levi's Stadium", "NRG Stadium", "Lincoln Financial Field", "Gillette Stadium"],
        key="stadium",
        label_visibility="collapsed",
    )
    
    st.markdown("<div class='sidebar-section'><h3>📅 Match Day</h3></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        match_date = st.date_input("Date", date.today(), key="match_date", label_visibility="collapsed")
    with col2:
        match_time = st.time_input("Time", datetime.now().time().replace(hour=20, minute=0), key="match_time", label_visibility="collapsed")
    
    st.markdown("<div class='sidebar-section'><h3>🌐 Language</h3></div>", unsafe_allow_html=True)
    language = st.selectbox(
        "Language",
        ["English", "Spanish", "French", "German", "Portuguese", "Arabic"],
        key="language",
        label_visibility="collapsed",
    )
    
    st.markdown("<div class='sidebar-section'><h3>👤 Your Role</h3></div>", unsafe_allow_html=True)
    role = st.radio(
        "Role",
        ["😊 Fan", "📋 Organizer", "🦺 Volunteer", "👔 Staff"],
        key="role",
        label_visibility="collapsed",
        index=0,
    )
    # Map display role to internal role
    role_map = {
        "😊 Fan": "fan",
        "📋 Organizer": "organizer",
        "🦺 Volunteer": "volunteer",
        "👔 Staff": "staff",
    }
    user_role = role_map[role]

# ── Initialize session state ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "assistant" not in st.session_state:
    st.session_state.assistant = StadiumAssistant(api_key=os.environ.get("GEMINI_API_KEY"))

# ── API Key Warning (hidden from main UI, only in backend) ──
if not os.getenv("GEMINI_API_KEY"):
    st.warning("⚠️ GEMINI_API_KEY not found. Add it to your .env file.", icon="⚠️")

# ── Chat Display ──
st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)

# Show welcome message if no messages
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align: center; padding: 3rem 1rem; color: #9E9E9E;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">⚽</div>
        <div style="font-size: 1.1rem; font-weight: 500; color: #616161;">Ask me anything about FIFA World Cup 2026 stadiums!</div>
        <div style="font-size: 0.85rem; margin-top: 0.5rem; color: #9E9E9E;">
            Try: "What's the best route to Gate A?"<br>
            or "How crowded will it be at halftime?"
        </div>
    </div>
    """, unsafe_allow_html=True)

# Display chat messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-bubble">{msg["content"]}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Input Area (fixed at bottom) ──
st.markdown('<div class="input-area">', unsafe_allow_html=True)

def handle_submit():
    user_msg = st.session_state.user_input.strip()
    if not user_msg:
        return
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_msg})
    
    # Get AI response
    with st.spinner("Thinking..."):
        response = st.session_state.assistant.prepare_response(
            user_query=user_msg,
            user_role=user_role,
            stadium=stadium,
            match_date=str(match_date) if match_date else "",
            match_time=str(match_time) if match_time else "",
            language=language,
            conversation_history=st.session_state.messages[:-1],
        )
    
    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})

with st.form(key="chat_form", clear_on_submit=True):
    cols = st.columns([6, 1])
    with cols[0]:
        st.text_input(
            "Message",
            placeholder="Ask about stadiums, routes, crowds, or match day...",
            key="user_input",
            label_visibility="collapsed",
        )
    with cols[1]:
        submitted = st.form_submit_button("➤", use_container_width=True, type="primary")
    
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