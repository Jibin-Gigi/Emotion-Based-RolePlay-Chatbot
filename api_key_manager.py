import streamlit as st
import google.generativeai as genai
from constants import API_KEY_STATE, GENAI_CONFIGURED_STATE

def get_api_key_securely() -> bool:
    """
    Handles the secure input and configuration of the Gemini API key.
    
    Returns:
        bool: True if the API key is successfully configured, False otherwise.
    """
    # Check if key is already in session state and configured
    if st.session_state.get(GENAI_CONFIGURED_STATE, False):
        return True

    st.sidebar.subheader("🔒 API Key Configuration")
    api_key = st.sidebar.text_input(
        "Enter your Gemini API Key:", 
        type="password", 
        key="api_key_input_widget"
    )

    if api_key:
        try:
            # Attempt to configure and test the key
            genai.configure(api_key=api_key)
            # Test the key by trying to list models (simpler than get_model)
            # This validates the key without needing the full model path
            list(genai.list_models())
            
            # Store key securely in session state (never on disk/logs)
            st.session_state[API_KEY_STATE] = api_key
            st.session_state[GENAI_CONFIGURED_STATE] = True
            st.sidebar.success("Gemini API Key configured successfully!")
            st.rerun() # Rerun to remove the input box and continue with the app
            return True
        except Exception as e:  # Changed from APIError to Exception
            # Check if it's an API-related error
            error_msg = str(e).lower()
            if 'api' in error_msg or 'key' in error_msg or 'invalid' in error_msg or 'permission' in error_msg:
                st.sidebar.error(f"Invalid API Key: {e}")
            else:
                st.sidebar.error(f"An error occurred during configuration: {e}")
            return False
    else:
        st.sidebar.warning("Please enter your Gemini API Key to start the app.")
        return False


def reset_session_and_delete_key():
    """
    Clears all session state, effectively deleting the API key and chat history.
    """
    if st.session_state.get(API_KEY_STATE):
        # Explicitly delete the key and configuration flag
        del st.session_state[API_KEY_STATE]
    if st.session_state.get(GENAI_CONFIGURED_STATE):
        del st.session_state[GENAI_CONFIGURED_STATE]
        
    for k in list(st.session_state.keys()):
        del st.session_state[k]
        
    st.success("Session ended. All data (including API key) cleared.")
    st.rerun()