import os
import streamlit as st
from banglaspeech2text import Speech2Text
from typing import Optional

# Cache the Speech2Text model for better performance
@st.cache_resource
def load_bangla_model():
    """Load BanglaSpeech2Text model"""
    try:
        # Initialize the BanglaSpeech2Text model
        stt = Speech2Text()
        return stt
    except Exception as e:
        st.error(f"Error loading BanglaSpeech2Text model: {e}")
        return None

def bangla_speech_to_text(audio_file_path: str) -> Optional[str]:
    """Convert Bengali speech to text using BanglaSpeech2Text package"""
    try:
        # Load the model
        stt = load_bangla_model()
        if stt is None:
            return None
        
        # Perform speech-to-text conversion
        transcription = stt(audio_file_path)
        
        # Clean up the transcription
        if transcription:
            transcription = transcription.strip()
            return transcription if transcription else None
        
        return None
        
    except Exception as e:
        st.error(f"Error in BanglaSpeech2Text transcription: {e}")
        return None

# Test function for the model
def test_bangla_model():
    """Test if the BanglaSpeech2Text model is working"""
    try:
        stt = load_bangla_model()
        if stt is not None:
            st.success("✅ BanglaSpeech2Text model loaded successfully!")
            st.info("📝 Model is ready for Bengali speech recognition")
            return True
        else:
            st.error("❌ Failed to load BanglaSpeech2Text model")
            return False
    except Exception as e:
        st.error(f"❌ Error testing BanglaSpeech2Text model: {e}")
        return False

# Additional utility functions for Bangla text processing
def clean_bangla_text(text: str) -> str:
    """Clean and format Bengali text"""
    if not text:
        return ""
    
    # Remove extra spaces and clean up
    text = ' '.join(text.split())
    
    # Add any specific Bengali text cleaning rules here
    return text

def is_bangla_text(text: str) -> bool:
    """Check if text contains Bengali characters"""
    if not text:
        return False
    
    # Bengali Unicode range: U+0980–U+09FF
    for char in text:
        if '\u0980' <= char <= '\u09FF':
            return True
    return False
