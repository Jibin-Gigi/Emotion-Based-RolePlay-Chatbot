# filename: app.py
import streamlit as st
import io
from PIL import Image

# Import utility functions and constants
from constants import (
    OPPOSITE_EMOTION, OPPOSITE_GENDER, 
    GENAI_CONFIGURED_STATE, PENDING_MESSAGE_STATE, PERSONA_PROMPT_STATE, 
    CHAR_PROFILE_STATE, CONVERSATION_STATE, CHAR_NAME_STATE
)
from api_key_manager import get_api_key_securely, reset_session_and_delete_key
from llm_service import analyze_image, create_character, chat_with_character

# -----------------------
# Utility: short character blurb (kept here as it's purely presentation logic)
# -----------------------
def build_brief(profile_text: str, max_len: int = 160) -> str:
    if not profile_text:
        return ""
    for line in profile_text.splitlines():
        candidate = line.strip()
        if candidate:
            brief = candidate
            break
    else:
        brief = profile_text.strip()
    
    brief = brief.replace("\n", " ")
    if len(brief) > max_len:
        brief = brief[: max_len - 1].rstrip() + "…"
    return brief


def queue_user_message():
    message_text = (st.session_state.get('user_input_chat') or '').strip()
    if message_text:
        st.session_state[PENDING_MESSAGE_STATE] = message_text


st.set_page_config(page_title="Emotion-to-Character Roleplay Chatbot", layout="centered")
st.title("Emotion-to-Character Roleplay Chatbot")
st.markdown(
    "This app uses your photo (or selection) to determine your emotion, then creates a chatbot character with the **opposite gender** and **opposite emotion** to roleplay with."
)
st.markdown("---")

# 1. API Key Check (Always runs first)
if not get_api_key_securely():
    # If the key isn't configured, stop the app execution here.
    st.info("The application awaits a valid Gemini API key in the sidebar. Your key is stored only in the browser session.")
    st.stop()


# 2. Main Application Logic
st.markdown("### 📸 Character Creation")
st.markdown("⚠️ **Privacy Note:** Your photo and chat messages are sent to the Gemini API. Your API key and data are **not saved** by this application after the session ends.")

# Camera input
img_file = st.camera_input("Take a selfie 📸", key='camera_input_widget')
analysis_done = False
primary_emotion = None
selected_gender = None

if img_file is not None:
    # Convert to PIL Image for display and analysis
    img_pil = Image.open(io.BytesIO(img_file.getvalue())).convert("RGB")
    st.image(img_pil, caption="Captured image", use_container_width=True)

    # Run analysis (Gemini vision)
    with st.spinner("Analyzing emotion and gender..."):
        analysis = analyze_image(img_pil)
    
    primary_emotion = analysis.get('dominant_emotion', 'unknown')
    detected_gender = analysis.get('gender', 'unknown')
    analysis_done = True
    
    
if analysis_done or st.session_state.get(PERSONA_PROMPT_STATE):
    
    st.markdown("---")

    # Emotion result (or manual fallback)
    if primary_emotion in ('unknown', None):
        st.subheader("1. Confirm Your Emotion")
        primary_emotion = st.selectbox(
            "Select your dominant emotion:",
            list(OPPOSITE_EMOTION.keys()),
            index=2 if primary_emotion != 'unknown' else 0, # Default to "sad" or first
            key='emotion_selectbox'
        )
    else:
        st.write(f"Your Detected Emotion: **{primary_emotion.upper()}**")

    # Gender selection (manual or detected)
    st.subheader("2. Confirm Your Gender")
    if detected_gender in ("unknown", None):
        selected_gender = st.selectbox(
            "Your gender (used to create an opposite-gender character):",
            list(OPPOSITE_GENDER.keys()),
            index=0,
            key='gender_selectbox'
        )
    else:
        selected_gender = detected_gender
        st.write(f"Detected Gender: **{selected_gender}**")

    # Determine opposites
    opposite_emotion = OPPOSITE_EMOTION.get(primary_emotion.lower(), 'neutral')
    opposite_gender = OPPOSITE_GENDER.get(selected_gender, 'Other')

    st.write(f"The chatbot character will be a **{opposite_gender}** with a **{opposite_emotion}** demeanor. ")

    # Character name
    st.subheader("3. Name Your Character")
    char_name = st.text_input("Choose a name for your character:", value="Alex", key='char_name_input')

    # Character creation button
    if st.button("Create Character & Start Chat", key='create_char_button'):
        # Reset chat history when creating a new character
        st.session_state.pop(PERSONA_PROMPT_STATE, None) 
        
        with st.spinner("Creating character..."):
            char_data = create_character(char_name, opposite_gender, opposite_emotion)
        
        if char_data is not None:
            # Store character data in session state
            st.session_state[PERSONA_PROMPT_STATE] = char_data['persona_prompt']
            st.session_state[CHAR_PROFILE_STATE] = char_data['profile_text']
            st.session_state[CONVERSATION_STATE] = [("System", "A new character has been created!")]
            st.session_state[CHAR_NAME_STATE] = char_name
            st.success("Character created. Start chatting below!")
            st.rerun() # Rerun to start the chat interface

# 3. Chat Interface
if st.session_state.get(PERSONA_PROMPT_STATE):
    
    st.markdown("---")
    st.subheader(f"Chat with {st.session_state.get(CHAR_NAME_STATE, 'your character')}")
    
    # Display the character profile
    if st.session_state.get(CHAR_PROFILE_STATE):
        with st.container(border=True):
            st.markdown("**Character description:**")
            st.info(st.session_state.get(CHAR_PROFILE_STATE, ''))
    
    # Process any pending message
    pending_msg = st.session_state.pop(PENDING_MESSAGE_STATE, None)
    if pending_msg:
        st.session_state[CONVERSATION_STATE].append(("User", pending_msg))
        
        # Get response from LLM
        with st.spinner("Character is thinking..."):
            response = chat_with_character(
                st.session_state[PERSONA_PROMPT_STATE],
                st.session_state[CONVERSATION_STATE],
                pending_msg,
            )
        
        st.session_state[CONVERSATION_STATE].append(("Character", response))
        st.session_state['user_input_chat'] = "" # Clear input widget value
        st.rerun() # Re-run to display the new messages
    
    # Display conversation history
    chat_container = st.container(height=300, border=True)
    for role, text in st.session_state.get(CONVERSATION_STATE, []):
        if role == "User":
            chat_container.chat_message("user").write(text)
        elif role == "Character" or role == "System":
            # Using character's name for their messages
            char_label = st.session_state.get(CHAR_NAME_STATE, 'Character') if role == "Character" else "System"
            # Use 'ai' icon for character/system messages
            chat_container.chat_message("ai", avatar="🤖").markdown(f"**{char_label}:** {text}")

    # User input for chat
    st.text_input(
        "You:",
        key="user_input_chat",
        on_change=queue_user_message,
        placeholder="Type your message here...",
        # The submit button will trigger on_change and queue_user_message
        label_visibility="collapsed",
    )
    


# 4. Clear Button
st.markdown("---")
if st.button("End Session & Securely Delete Key"):
    reset_session_and_delete_key()