# filename: llm_service.py
import streamlit as st
import google.generativeai as genai
import io
import json
from constants import API_KEY_STATE


def get_gemini_client():
    api_key = st.session_state.get(API_KEY_STATE)
    if not api_key:
        raise ValueError("Gemini API Key is not configured.")
    
    # Configure on the fly for each run, using the secure key
    genai.configure(api_key=api_key)


def analyze_image(img_pil):
    get_gemini_client()
    try:
        buf = io.BytesIO()
        # Save as JPEG for better compatibility/size
        img_pil.save(buf, format="JPEG")
        img_bytes = buf.getvalue()

        prompt = (
            "Look at the person in the photo and infer two things: "
            "1) their dominant emotion as one of: angry, happy, sad, fear, disgust, surprise, neutral, contempt; "
            "2) perceived gender as one of: Man, Woman, Other. "
            "Respond ONLY as compact JSON like {\"emotion\":\"happy\",\"gender\":\"Man\"}."
        )
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        resp = model.generate_content([
            {"mime_type": "image/jpeg", "data": img_bytes},
            prompt,
        ])
        
        text = resp.text.strip()
        # Robustly strip code fences
        if text.startswith("```json") and text.endswith("```"):
            text = text[len("```json"): -3].strip()
        
        data = json.loads(text)
        emotion = str(data.get("emotion", "unknown")).lower()
        gender = str(data.get("gender", "unknown"))
        
        return {"dominant_emotion": emotion, "gender": gender, "age": None}
    except Exception as e:
        st.warning(f"Image analysis failed: {e}")
        return {"dominant_emotion": "unknown", "gender": "unknown", "age": None}


def create_character(person_name, target_gender, target_emotion):
    get_gemini_client()
    profile_prompt = (
        f"You are a character creator. Your task is to generate a concise character profile. "
        f"The character's name is {person_name}, they are a {target_gender} and should embody the primary emotion '{target_emotion}'. "
        f"The character should be anyone from the world and their profession can be anything. They can be a professional, celebrity, normal person, army person, assassin, detective, financially instable one, etc.."
        f"They should have personality traits like shy, introvert, extrovert, funny, serious, mad, psycopathic, etc., according to their emotion, personlity, gender and profession."
        f"The profile must be exactly **three sentences** long and written in a simple, third-person perspective. "
        f"Sentence 1: State their name, age-range, profession, and city/region. "
        f"Sentence 2: Describe a routine habit and one hobby. "
        f"Sentence 3: Mention their one thing that everyone knows."
    )
    
    try:
        # First call to generate the concise profile
        model = genai.GenerativeModel('gemini-2.0-flash')
        profile_resp = model.generate_content(profile_prompt)
        final_profile = profile_resp.text.strip()

        # Second, more detailed prompt for the chat persona
        persona_prompt_template = (
            f"You will now roleplay as the following character:\n\n{final_profile}\n\n"
            "Your persona is defined by the profile above. Follow these rules strictly for all your responses:\n"
            "1. **Converse Naturally:** Respond like a real person, not a chatbot. Use casual language and realistic sentence structures.\n"
            "2. **Stay In-Character:** Your responses must align with your character's emotion and personality.Engage according to your persona and increase or decrease engagement as per the chats of the user.\n"
            "3. **Be Vague with Secrets:** If asked about your secrets or sensitive life events, be evasive. Hint at them without giving direct details.\n"
            "4. **Keep it Concise:** Limit responses to 1-3 sentences to simulate a real conversation. Unless your character is a talkative person.\n"
            "5. **No Stage Directions:** Do not use parentheses, brackets, or any other meta-text to describe your actions or feelings.\n"
            "6. **Acknowledge User:** Respond directly to the user's question or statement without repeating it.\n"
            "7. **Know Your Profession:** You should be knowledgeable about your character's profession and surroundings (e.g., if you are a doctor in USA, you know about local hospitals).\n"
        )
        
        return {'profile_text': final_profile, 'persona_prompt': persona_prompt_template}
    except Exception as e:
        st.error(f"Failed to create character: {e}")
        return None

def chat_with_character(persona_prompt, conversation_history, user_message):
    get_gemini_client()
    full_prompt = (
        f"{persona_prompt}\n\n"
        f"Conversation history (last few turns):\n"
    )
    # Build a single prompt that includes persona + conversation history.
    # Limiting history for prompt size management
    for role, text in conversation_history[-8:]: 
        # Using a consistent format for the model
        full_prompt += f"{role}: {text}\n" 
    full_prompt += f"User: {user_message}\nCharacter:"
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        resp = model.generate_content(full_prompt)
        return resp.text
    except Exception as e:
        st.error(f"Chat failed: {e}")
        return "Sorry, I couldn't produce a response right now."