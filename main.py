import streamlit as st
import openai
from typing import List, Dict, Any

# -------------------------------------------------
# 🔑  API‑KEY HANDLING & APP CONFIGURATION
# -------------------------------------------------
# 1) Use st.secrets if the deployer supplied it
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]

# 2) Allow each user to paste a key at runtime (kept only in session)
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""

with st.sidebar:
    api_input = st.text_input("🔑 Enter your OpenAI API Key", type="password", value=st.session_state.openai_api_key)
    if api_input:
        st.session_state.openai_api_key = api_input
        openai.api_key = api_input
        st.success("API key set for this session.")

# -------------------------------------------------
# CONSTANTS
# -------------------------------------------------
AVAILABLE_MODELS = [
    "gpt-4.1",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-3.5-turbo-0125",
]

# -------------------------------------------------
# ROUTE FUNCTIONS (one per learning assistant mode)
# -------------------------------------------------

def call_writeup_model(messages: List[Dict[str, str]], model: str, temperature: float):
    return _chat(messages, model, temperature)


def call_self_assessment_model(messages: List[Dict[str, str]], model: str, temperature: float):
    prefix = "You are an AI self-assessment coach. Help users reflect concisely on their work."
    return _chat([{"role": "system", "content": prefix}] + messages, model, temperature)


def call_jigsaw_model(messages: List[Dict[str, str]], model: str, temperature: float):
    prefix = "You are an AI learning‑facilitator guiding a Jigsaw cooperative activity."
    return _chat([{"role": "system", "content": prefix}] + messages, model, temperature)


def call_feedback_on_feedback_model(messages: List[Dict[str, str]], model: str, temperature: float):
    prefix = "You are an AI reviewer providing meta-feedback on peer feedback quality."
    return _chat([{"role": "system", "content": prefix}] + messages, model, temperature)


def call_clarification_model(messages: List[Dict[str, str]], model: str, temperature: float):
    prefix = "You help refine and clarify peer feedback by asking targeted follow-up questions."
    return _chat([{"role": "system", "content": prefix}] + messages, model, temperature)


# Shared OpenAI call helper

def _chat(messages: List[Dict[str, str]], model: str, temperature: float):
    if not openai.api_key:
        return "⚠️ Please provide an OpenAI API key in the sidebar."
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as exc:
        return f"⚠️ Error querying OpenAI: {exc}"


FUNCTION_ROUTES = {
    "Write-up": call_writeup_model,
    "Self-assessment": call_self_assessment_model,
    "Jigsaw/cooperation": call_jigsaw_model,
    "AI Feedback on feedback": call_feedback_on_feedback_model,
    "Further Clarification on peer feedback": call_clarification_model,
}

# -------------------------------------------------
# SESSION STATE INITIALISATION
# -------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "selector"
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []
if "function_choice" not in st.session_state:
    st.session_state.function_choice = None
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "model_choice" not in st.session_state:
    st.session_state.model_choice = AVAILABLE_MODELS[0]

# Rerun helper (handles new/old Streamlit)

def _trigger_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st.experimental, "rerun"):
        st.experimental_rerun()

# -------------------------------------------------
# PAGE 1 – FUNCTION SELECTOR
# -------------------------------------------------
if st.session_state.page == "selector":
    st.title("📚 Peer Feedback AI Assistants")

    st.markdown("### 1. Choose a Assistant")
    function_choice = st.selectbox("Which assistant are you testing?", list(FUNCTION_ROUTES.keys()))

    st.markdown("### 2. Model settings")
    model_choice = st.selectbox("GPT model", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(st.session_state.model_choice))
    temperature = st.slider("Temperature (creativity)", 0.0, 1.0, st.session_state.temperature, 0.05)

    start_disabled = not bool(openai.api_key)
    if st.button("🚀 Start", disabled=start_disabled):
        st.session_state.function_choice = function_choice
        st.session_state.model_choice = model_choice
        st.session_state.temperature = temperature
        st.session_state.page = "chat"
        _trigger_rerun()

    if start_disabled:
        st.info("Enter your OpenAI API key in the sidebar to enable the chat.")

# -------------------------------------------------
# PAGE 2 – CHAT INTERFACE
# -------------------------------------------------
if st.session_state.page == "chat":
    st.sidebar.title("⚙️ Settings")
    st.sidebar.write(f"**Mode:** {st.session_state.function_choice}")
    st.sidebar.selectbox("Model", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(st.session_state.model_choice), key="model_choice")
    st.sidebar.slider("Temperature", 0.0, 1.0, st.session_state.temperature, 0.05, key="temperature")

    if st.sidebar.button("🔄 Reset conversation"):
        st.session_state.messages = []

    st.title(f"💬 {st.session_state.function_choice} Chatbot")

    # Chat history
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    user_text = st.chat_input("Type your message…")
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        route_fn = FUNCTION_ROUTES[st.session_state.function_choice]
        reply = route_fn(
            messages=st.session_state.messages,
            model=st.session_state.model_choice,
            temperature=st.session_state.temperature,
        )

        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

    st.divider()
    if st.button("⬅️ Back"):
        st.session_state.page = "selector"
        _trigger_rerun()

