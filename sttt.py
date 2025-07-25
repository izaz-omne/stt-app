import streamlit as st
import os
from utilss import speech_to_text
from bangla_stt_cpu import bangla_speech_to_text, test_bangla_model, clean_bangla_text
# from bangla_stt_large import bangla_speech_to_text, test_bangla_model, clean_bangla_text
from audio_recorder_streamlit import audio_recorder
from streamlit_float import *
import hashlib
import speech_recognition as sr

# Float feature initialization
float_init()

def initialize_session_state():
    if "transcripts" not in st.session_state:
        st.session_state.transcripts = []
    if "last_audio_hash" not in st.session_state:
        st.session_state.last_audio_hash = None
    if "is_option_change" not in st.session_state:
        st.session_state.is_option_change = False

initialize_session_state()

st.title("Enhanced Speech-to-Text App 🎤")
st.markdown("*Now with Bengali language support!*")

# Transcription engine selection with BanglaSpeech2Text
ENGINE_OPTIONS = ["Deepgram", "Python SpeechRecognition", "BanglaSpeech2Text"]
selected_engine = st.selectbox(
    "Choose transcription engine:",
    options=ENGINE_OPTIONS,
    index=0,
    help="BanglaSpeech2Text is specifically optimized for Bengali language"
)

# Language selection with conditional options
if selected_engine == "BanglaSpeech2Text":
    # For BanglaSpeech2Text, only Bengali is supported
    LANGUAGE_OPTIONS = {
        "Bengali (বাংলা)": "bn-BD"
    }
    selected_language = "Bengali (বাংলা)"
    language_code = "bn-BD"
    st.info("🇧🇩 BanglaSpeech2Text is optimized for Bengali language only")
    
    # Model size selection for BanglaSpeech2Text
    BANGLA_MODEL_SIZES = {
        "Tiny (~39MB)": "tiny",
        "Base (~74MB) - Recommended": "base", 
        "Small (~244MB)": "small",
        "Medium (~769MB)": "medium",
        "Large (~1550MB)": "large"
    }
    
    selected_bangla_model = st.selectbox(
        "Choose BanglaSpeech2Text model size:",
        options=list(BANGLA_MODEL_SIZES.keys()),
        index=1,  # Default to base model
        help="Smaller models download faster but may have lower accuracy. Base model (~74MB) is recommended for good balance."
    )
    bangla_model_size = BANGLA_MODEL_SIZES[selected_bangla_model]
    
    # Test the model on first load
    if st.button("🧪 Test BanglaSpeech2Text Model"):
        with st.spinner(f"Testing BanglaSpeech2Text {bangla_model_size} model..."):
            test_bangla_model(bangla_model_size)
            
else:
    # For other engines, show all supported languages
    DEEPGRAM_LANGUAGES = {
        "English (US)": "en-US",
        "English (UK)": "en-GB",
        "Spanish": "es",
        "French": "fr",
        "German": "de",
        "Italian": "it",
        "Portuguese": "pt",
        "Hindi": "hi",
        "Chinese (Mandarin)": "zh",
        "Japanese": "ja",
        "Korean": "ko",
        "Bengali (বাংলা)": "bn-BD"  # Added Bengali for other engines too
    }

    selected_language = st.selectbox(
        "Choose language for transcription:",
        options=list(DEEPGRAM_LANGUAGES.keys()),
        index=0
    )
    language_code = DEEPGRAM_LANGUAGES[selected_language]

# Show Deepgram models dropdown only when Deepgram is selected
if selected_engine == "Deepgram":
    DEEPGRAM_MODELS = {
        "Nova-3 (best, default)": "nova-3",
        "Nova-2 (fast, legacy)": "nova-2",
        "Base (general)": "base"
    }

    selected_model = st.selectbox(
        "Choose Deepgram model:",
        options=list(DEEPGRAM_MODELS.keys()),
        index=0
    )
    model_code = DEEPGRAM_MODELS[selected_model]

def get_audio_hash(audio_bytes):
    if audio_bytes is None:
        return None
    return hashlib.md5(audio_bytes).hexdigest()

def python_stt(audio_file_path, language="en-US"):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file_path) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language=language)
    except Exception as e:
        st.error(f"Python STT error: {e}")
        return None

# Track last processed audio hash and reset if options change
if (
    st.session_state.get("last_engine") != selected_engine or
    st.session_state.get("last_lang") != selected_language or
    (selected_engine == "Deepgram" and st.session_state.get("last_model") != selected_model) or
    (selected_engine == "BanglaSpeech2Text" and st.session_state.get("last_bangla_model") != bangla_model_size)
):
    st.session_state.is_option_change = True
else:
    st.session_state.is_option_change = False

st.session_state["last_engine"] = selected_engine
st.session_state["last_lang"] = selected_language
if selected_engine == "Deepgram":
    st.session_state["last_model"] = selected_model
elif selected_engine == "BanglaSpeech2Text":
    st.session_state["last_bangla_model"] = bangla_model_size

# Create footer container for the microphone
footer_container = st.container()
with footer_container:
    audio_bytes = audio_recorder(
        pause_threshold=2.5,
        sample_rate=16000,
        recording_color="#e74c3c",
        neutral_color="#34495e",
        icon_size="2x"
    )

audio_hash = get_audio_hash(audio_bytes)

# Debug information (can be commented out in production)
with st.expander("🔍 Debug Information", expanded=False):
    st.write(f"Audio bytes present: {audio_bytes is not None}")
    st.write(f"Current hash: {audio_hash}")
    st.write(f"Last hash: {st.session_state.get('last_audio_hash')}")
    st.write(f"Current engine: {selected_engine}")
    st.write(f"Current language: {selected_language}")
    st.write(f"Is option change: {st.session_state.get('is_option_change', False)}")

if audio_bytes and (audio_hash != st.session_state.get("last_audio_hash")) and not st.session_state.is_option_change:
    with st.spinner(f"Transcribing with {selected_engine}..."):
        # Determine file extension based on engine
        if selected_engine == "Python SpeechRecognition":
            temp_file_path = "temp_audio.wav"
        elif selected_engine == "BanglaSpeech2Text":
            temp_file_path = "temp_audio.wav"  # BanglaSpeech2Text works better with WAV
        else:
            temp_file_path = "temp_audio.mp3"
            
        # Save audio to temporary file
        with open(temp_file_path, "wb") as f:
            f.write(audio_bytes)

        # Transcribe based on selected engine
        transcript = None
        
        if selected_engine == "Deepgram":
            transcript = speech_to_text(temp_file_path, language_code, model_code)
            
        elif selected_engine == "Python SpeechRecognition":
            try:
                transcript = python_stt(temp_file_path, language_code)
            except Exception as e:
                st.warning("Python STT only supports WAV audio. Please try again.")
                transcript = None
                
        elif selected_engine == "BanglaSpeech2Text":
            try:
                transcript = bangla_speech_to_text(temp_file_path, bangla_model_size)
                if transcript:
                    transcript = clean_bangla_text(transcript)
                    st.success(f"🇧🇩 Bengali transcription completed with {bangla_model_size} model!")
            except Exception as e:
                st.error(f"BanglaSpeech2Text error: {e}")
                transcript = None

        # Process transcript
        if transcript and len(transcript.strip()) > 0:
            st.session_state.transcripts.append({
                "text": transcript,
                "engine": selected_engine,
                "language": selected_language,
                "timestamp": st.session_state.get("transcript_count", len(st.session_state.transcripts))
            })
        else:
            st.warning("Could not transcribe audio. Please try speaking again.")

        # Clean up temporary file
        try:
            os.remove(temp_file_path)
        except:
            pass

        st.session_state.last_audio_hash = audio_hash

# Display all transcripts in a chat UI
st.subheader("📝 Transcription Chat History")

if st.session_state.transcripts:
    for i, transcript_data in enumerate(st.session_state.transcripts):
        with st.chat_message("user"):
            # Handle both old format (string) and new format (dict)
            if isinstance(transcript_data, dict):
                text = transcript_data["text"]
                engine = transcript_data.get("engine", "Unknown")
                language = transcript_data.get("language", "Unknown")
                
                # Display transcript with metadata
                st.write(text)
                st.caption(f"🔧 Engine: {engine} | 🌐 Language: {language}")
                
                # Special styling for Bengali text
                if engine == "BanglaSpeech2Text":
                    st.markdown(f"<div style='background-color: #e8f5e8; padding: 10px; border-radius: 5px; margin: 5px 0;'>"
                              f"<strong>Bengali:</strong> {text}</div>", 
                              unsafe_allow_html=True)
            else:
                # Legacy format - just display the text
                st.write(transcript_data)
else:
    st.info("🎙️ Start recording to see your transcriptions here!")

# Clear history button
if st.session_state.transcripts:
    if st.button("🗑️ Clear History"):
        st.session_state.transcripts = []
        st.session_state.last_audio_hash = None
        st.rerun()

# Float the footer container
footer_container.float("bottom: 0rem;")

# Add information about the engines
with st.sidebar:
    st.header("🔧 Engine Information")
    
    st.subheader("BanglaSpeech2Text")
    st.write("- Specialized for Bengali language")
    st.write("- Multiple model sizes available")
    st.write("- CPU-only mode (no GPU required)")
    st.write("- Optimized for Bengali speech patterns")
    st.write("- Model sizes:")
    st.write("  • Tiny: ~39MB")
    st.write("  • Base: ~74MB (Recommended)")
    st.write("  • Small: ~244MB")
    st.write("  • Medium: ~769MB")
    st.write("  • Large: ~1550MB")
    
    st.subheader("Deepgram")
    st.write("- Multi-language support")
    st.write("- Fast and accurate")
    st.write("- Multiple model options")
    st.write("- Commercial API")
    
    st.subheader("Python SpeechRecognition")
    st.write("- Uses Google's speech API")
    st.write("- Free but limited")
    st.write("- Requires WAV format")
    st.write("- Good for testing")
    
    st.markdown("---")
    st.markdown("**💡 Tip:** Use BanglaSpeech2Text for the best Bengali transcription results!")
