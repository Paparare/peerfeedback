import streamlit as st
import openai
from typing import List, Dict, Any

# --------------- CONFIG -----------------
# You can also let users set their key via st.secrets or st.text_input
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]

# Default available GPT models – extend if needed
AVAILABLE_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-3.5-turbo-0125",
]

# --------------- FUNCTION ROUTERS -----------------

def call_writeup_model(messages: List[Dict[str, str]], model: str, temperature: float):
    """Route conversation to Write‑up assistant."""
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def call_self_assessment_model(messages: List[Dict[str, str]], model: str, temperature: float):
    """Route conversation to Self‑assessment assistant."""
    prompt_prefix = (
        "You are an AI self‑assessment coach. Help users reflect on their work.\n"
        "When appropriate, ask probing questions and give concise feedback."
    )
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": prompt_prefix}] + messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def call_jigsaw_model(messages: List[Dict[str, str]], model: str, temperature: float):
    """Route conversation to Jigsaw/cooperation facilitator."""
    prompt_prefix = (
        "You are an AI learning‑facilitator helping a small group of students use a Jigsaw strategy."
    )
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": prompt_prefix}] + messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def call_feedback_on_feedback_model(messages: List[Dict[str, str]], model: str, temperature: float):
    """Route conversation to AI feedback‑on‑feedback assistant."""
    prompt_prefix = "You are an AI reviewer who gives meta‑feedback on peer feedback quality."
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": prompt_prefix}] + messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def call_further_clarification_model(messages: List[Dict[str, str]], model: str, temperature: float):
    """Route conversation to Further‑clarification assistant."""
    prompt_prefix = "You help refine and clarify peer feedback by asking targeted follow‑up questions."
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": prompt_prefix}] + messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


# Map UI label → function
FUNCTION_ROUTES = {
    "Write-up": call_writeup_model,
    "Self-assessment": call_self_assessment_model,
    "Jigsaw/cooperation": call_jigsaw_model,
    "AI Feedback on feedback": call_feedback_on_feedback_model,
    "Further Clarification on peer feedback": call_further_clarification_model,
}

# --------------- SESSION INITIALISATION -----------------
if "page" not in st.session_state:
    st.session_state.page = "selector"
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []  # conversation log
if "function_choice" not in st.session_state:
    st.session_state.function_choice = None
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "model_choice" not in st.session_state:
    st.session_state.model_choice = AVAILABLE_MODELS[0]

# --------------- PAGE 1 – FUNCTION SELECTOR -----------------
if st.session_state.page == "selector":
    st.title("📚 Educational Assistant Workbench")

    st.markdown("### Step 1 – Choose a function:")
    function_choice = st.selectbox("Select what you want to do", list(FUNCTION_ROUTES.keys()))

    st.markdown("### Step 2 – Model configuration:")
    model_choice = st.selectbox("Choose GPT model", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(st.session_state.model_choice))
    temperature = st.slider("Temperature (creativity)", 0.0, 1.0, st.session_state.temperature, 0.05)

    start = st.button("🚀 Start")

    if start:
        st.session_state.function_choice = function_choice
        st.session_state.temperature = temperature
        st.session_state.model_choice = model_choice
        st.session_state.page = "chat"
        st.experimental_rerun()

# --------------- PAGE 2 – CHAT INTERFACE -----------------
if st.session_state.page == "chat":
    st.sidebar.title("⚙️ Settings")
    st.sidebar.write(f"**Mode:** {st.session_state.function_choice}")
    st.sidebar.selectbox("Model", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(st.session_state.model_choice), key="model_choice")
    st.sidebar.slider("Temperature", 0.0, 1.0, st.session_state.temperature, 0.05, key="temperature")

    if st.sidebar.button("🔄 Reset Conversation"):
        st.session_state.messages = []

    st.title(f"💬 {st.session_state.function_choice} Chatbot")

    # Display chat history
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Chat input
    user_input = st.chat_input(placeholder="Type your message…")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call the correct model function
        route_fn = FUNCTION_ROUTES[st.session_state.function_choice]
        try:
            assistant_reply = route_fn(
                messages=st.session_state.messages,
                model=st.session_state.model_choice,
                temperature=st.session_state.temperature,
            )
        except Exception as e:
            assistant_reply = f"⚠️ Error querying OpenAI: {e}"

        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

        with st.chat_message("assistant"):
            st.markdown(assistant_reply)

    st.divider()
    if st.button("⬅️ Back to Function Selector"):
        st.session_state.page = "selector"
        st.experimental_rerun()
