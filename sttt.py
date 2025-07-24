import streamlit as st
import os
from utilss import speech_to_text
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

st.title("Speech-to-Text App 🎤")

# Transcription engine selection
ENGINE_OPTIONS = ["Deepgram", "Python SpeechRecognition"]
selected_engine = st.selectbox(
    "Choose transcription engine:",
    options=ENGINE_OPTIONS,
    index=0
)

# Deepgram supported languages (add more as needed)
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
    "Korean": "ko"
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
    (selected_engine == "Deepgram" and st.session_state.get("last_model") != selected_model)
):
    st.session_state.is_option_change = True
else:
    st.session_state.is_option_change = False

st.session_state["last_engine"] = selected_engine
st.session_state["last_lang"] = selected_language
if selected_engine == "Deepgram":
    st.session_state["last_model"] = selected_model

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

# Add these debug lines after your audio_recorder
# st.write("Debug:")
# st.write(f"Audio bytes present: {audio_bytes is not None}")
# st.write(f"Current hash: {audio_hash}")
# st.write(f"Last hash: {st.session_state.get('last_audio_hash')}")
# st.write(f"Current engine: {selected_engine}")
# st.write(f"Current language: {selected_language}")
# st.write(f"Is option change: {st.session_state.get('is_option_change', False)}")

if audio_bytes and (audio_hash != st.session_state.get("last_audio_hash")) and not st.session_state.is_option_change:
    with st.spinner("Transcribing..."):
        temp_file_path = "temp_audio.wav" if selected_engine == "Python SpeechRecognition" else "temp_audio.mp3"
        with open(temp_file_path, "wb") as f:
            f.write(audio_bytes)

        if selected_engine == "Deepgram":
            transcript = speech_to_text(temp_file_path, language_code, model_code)
        else:
            try:
                transcript = python_stt(temp_file_path, language_code)
            except Exception as e:
                st.warning("Python STT only supports WAV audio. Please try again.")
                transcript = None

        if transcript and len(transcript.strip()) > 0:
            st.session_state.transcripts.append(transcript)
        else:
            st.warning("Could not transcribe audio. Please try speaking again.")

        try:
            os.remove(temp_file_path)
        except:
            pass

        st.session_state.last_audio_hash = audio_hash

# Display all transcripts in a chat UI
st.subheader("Transcription Chat History")
for t in st.session_state.transcripts:
    with st.chat_message("user"):
        st.write(t)

# Float the footer container and provide CSS to target it with
footer_container.float("bottom: 0rem;")
