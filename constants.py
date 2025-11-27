# Utility: opposite mapping for emotion
OPPOSITE_EMOTION = {
    'angry': 'calm',
    'happy': 'sad',
    'sad': 'happy',
    'fear': 'confident',
    'disgust': 'admiration',
    'surprise': 'boredom',
    'neutral': 'emotional',
    'contempt': 'respectful',
}

# Utility: opposite mapping for gender
OPPOSITE_GENDER = {
    'Man': 'Woman',
    'Woman': 'Man',
    'Other': 'Other' 
}

# Constants for session state keys
API_KEY_STATE = 'gemini_api_key'
GENAI_CONFIGURED_STATE = 'genai_configured'
PENDING_MESSAGE_STATE = 'pending_user_message'
PERSONA_PROMPT_STATE = 'persona_prompt'
CHAR_PROFILE_STATE = 'char_profile'
CONVERSATION_STATE = 'conversation'
CHAR_NAME_STATE = 'char_name'