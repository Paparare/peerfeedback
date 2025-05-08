import streamlit as st
import openai
from typing import List, Dict, Any

# --------------- CONFIG -----------------
# Users can keep keys in st.secrets or supply via a textbox
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]

# --------------- CONSTANTS -----------------
AVAILABLE_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-3.5-turbo-0125",
]

# --------------- ROUTE FUNCTIONS -----------------

def call_writeup_model(messages: List[Dict[str, str]], model: str, temperature: float):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def call_self_assessment_model(messages: List[Dict[str, str]], model: str, temperature: float):
    prefix = "You are an AI self‑assessment coach. Help users reflect concisely on their work."
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": prefix}] + messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def call_jigsaw_model(messages: List[Dict[str, str]], model: str, temperature: float):
    prefix = "You are an AI learning‑facilitator guiding a Jigsaw cooperative activity."
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": prefix}] + messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def call_feedback_on_feedback_model(messages: List[Dict[str, str]], model: str, temperature: float):
    prefix = "You are an AI reviewer providing meta‑feedback on peer feedback quality."
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": prefix}] + messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def call_clarification_model(messages: List[Dict[str, str]], model: str, temperature: float):
    prefix = "You help refine and clarify peer feedback by asking targeted follow‑up questions."
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": prefix}] + messages,
        temperature=temperature,
    )
    return response.choices[0].message.content

FUNCTION_ROUTES = {
    "Write-up": call_writeup_model,
    "Self-assessment": call_self_assessment_model,
    "Jigsaw/cooperation": call_jigsaw_model,
    "AI Feedback on feedback": call_feedback_on_feedback_model,
    "Further Clarification on peer feedback": call_clarification_model,
}

# --------------- SESSION INIT -----------------
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

# Helper to rerun regardless of Streamlit version

def _trigger_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st.experimental, "rerun"):
        st.experimental_rerun()
    else:
        st.warning("⚠️ Cannot force rerun on this Streamlit version. Please refresh manually.")

# --------------- PAGE 1 – FUNCTION SELECTOR -----------------
if st.session_state.page == "selector":
    st.title("📚 Educational Assistant Workbench")

    st.markdown("### 1. Choose a function")
    function_choice = st.selectbox("What do you want to do?", list(FUNCTION_ROUTES.keys()))

    st.markdown("### 2. Model settings")
    model_choice = st.selectbox("GPT model", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(st.session_state.model_choice))
    temperature = st.slider("Temperature (creativity)", 0.0, 1.0, st.session_state.temperature, 0.05)

    if st.button("🚀 Start"):
        st.session_state.function_choice = function_choice
        st.session_state.model_choice = model_choice
        st.session_state.temperature = temperature
        st.session_state.page = "chat"
        _trigger_rerun()

# --------------- PAGE 2 – CHAT INTERFACE -----------------
if st.session_state.page == "chat":
    st.sidebar.title("⚙️ Settings")
    st.sidebar.write(f"**Mode:** {st.session_state.function_choice}")
    st.sidebar.selectbox("Model", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(st.session_state.model_choice), key="model_choice")
    st.sidebar.slider("Temperature", 0.0, 1.0, st.session_state.temperature, 0.05, key="temperature")

    if st.sidebar.button("🔄 Reset conversation"):
        st.session_state.messages = []

    st.title(f"💬 {st.session_state.function_choice} Chatbot")

    # History
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    user_text = st.chat_input("Type your message…")
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        route_fn = FUNCTION_ROUTES[st.session_state.function_choice]
        try:
            reply = route_fn(
                messages=st.session_state.messages,
                model=st.session_state.model_choice,
                temperature=st.session_state.temperature,
            )
        except Exception as e:
            reply = f"⚠️ Error querying OpenAI: {e}"

        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

    st.divider()
    if st.button("⬅️ Back"):
        st.session_state.page = "selector"
        _trigger_rerun()

