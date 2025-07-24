import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from gtts import gTTS
import tempfile
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cache clients for better performance
@st.cache_resource
def get_groq_client():
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        st.error("GROQ_API_KEY not found in environment variables!")
        return None
    
    return ChatGroq(
        groq_api_key=groq_api_key,
        model_name="llama-3.3-70b-versatile",
        temperature=0.3,  # Lower temperature for faster responses
        max_tokens=512,   # Reduced tokens for faster generation
        streaming=True    # Enable streaming for faster responses
    )

@st.cache_resource
def get_deepgram_client():
    # Replace this with your actual Deepgram API key
    deepgram_api_key = "0d154512e1c223e00f54840d6a73b9dee1c8cd41"  # Your API key
    if not deepgram_api_key:
        st.error("Please add your Deepgram API key!")
        return None
    
    return DeepgramClient(deepgram_api_key)

def speech_to_text(audio_file_path, language="en-US", model="nova-3"):
    """Convert speech to text using Deepgram API - optimized for free tier"""
    try:
        deepgram = get_deepgram_client()
        if not deepgram:
            return None
        
        with open(audio_file_path, "rb") as audio_file:
            buffer_data = audio_file.read()
        
        payload: FileSource = {
            "buffer": buffer_data,
        }
        
        # Use the selected language and model
        options = PrerecordedOptions(
            model=model,
            smart_format=True,
            language=language,
        )
        
        response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
        
        # Extract transcript from single alternative (Nova-2 limitation)
        channels = response.results.channels[0]
        if channels.alternatives and len(channels.alternatives) > 0:
            transcript = channels.alternatives[0].transcript.strip()
            return transcript if transcript else None
        
        return None
    
    except Exception as e:
        st.error(f"Error in speech to text: {e}")
        return None

def get_answer(messages):
    """Get AI response using Groq Llama-3.3-70b-versatile via LangChain - optimized for speed"""
    try:
        groq_client = get_groq_client()
        if not groq_client:
            return "Sorry, I'm having trouble connecting to the AI service."
        
        # Convert Streamlit messages to LangChain format (limit context for speed)
        langchain_messages = []
        
        # Add system message (shorter for faster processing)
        system_message = SystemMessage(content="""You are Aaladin AI — the voice-activated, web and mobile app development genie from AaladinAI.com.

        Aaladin specializes in:
        • Full-stack web & mobile development  
        • UI/UX design  
        • Automation tools and AI/ChatGPT integrations  
        • Cloud & DevOps solutions  
        • API development & browser extensions  
        The team works with Next.js, React, Flutter, Node.js, TypeScript, and tailors solutions for startups, enterprises, and innovators :contentReference[oaicite:1]{index=1}.

        Users speak to you via live-transcribed voice commands (Deepgram-backed), which may include informal phrasing. You interpret their intent, plan or build software solutions, and respond clearly and confidently—as if you’re their technical co-founder.

        Your roles:
        1. Analyze and refine the spoken request.
        2. Design appropriate architecture, code snippets, UI wireframes, or project outlines.
        3. Ask follow-up questions **only if needed** to clarify requirements.
        4. Deliver final outputs in ready-to-use formats (e.g., code with imports, comments, filenames).
        5. Keep answers concise, natural, and conversational—suitable for voice playback or visual consumption.

        Always:
        - Include relevant technology choices (e.g., Next.js + Tailwind CSS, Flutter, cloud, AI)
        - Align answers with Aaladin’s proven development methodology: planning, wireframing, design, coding, testing, deployment :contentReference[oaicite:2]{index=2}.
        - Reflect Aaladin’s brand identity: empowering, dependable, agile, and digitally transformative.

        Never:
        - Mention Deepgram, transcription, or the toolchain behind the voice interface.
        - Be overly formal or robotic.

        You are Aaladin AI — your voice, our power. Build something amazing.
""")
        langchain_messages.append(system_message)
        
        # Only use last 6 messages for context (3 exchanges) to speed up processing
        recent_messages = messages[-6:] if len(messages) > 6 else messages
        
        # Convert conversation history
        for message in recent_messages:
            if message["role"] == "user":
                langchain_messages.append(HumanMessage(content=message["content"]))
            elif message["role"] == "assistant":
                langchain_messages.append(AIMessage(content=message["content"]))
        
        # Get response from Groq
        response = groq_client.invoke(langchain_messages)
        return response.content
    
    except Exception as e:
        st.error(f"Error getting AI response: {e}")
        return "Sorry, I encountered an error while processing your request."

def text_to_speech(text):
    """Convert text to speech using gTTS - optimized for speed"""
    try:
        # Limit text length for faster generation
        if len(text) > 500:
            text = text[:500] + "..."
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file_path = temp_file.name
        temp_file.close()
        
        # Generate speech with optimized settings
        tts = gTTS(
            text=text, 
            lang='en', 
            slow=False,
            tld='com'  # Use .com for faster processing
        )
        tts.save(temp_file_path)
        
        return temp_file_path
    
    except Exception as e:
        st.error(f"Error in text to speech: {e}")
        return None

def autoplay_audio(file_path):
    """Auto-play audio file in Streamlit"""
    try:
        with open(file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        
        # Encode audio to base64
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        # Create HTML audio element with autoplay
        audio_html = f"""
        <audio autoplay="true" controls style="width: 100%;">
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        Your browser does not support the audio element.
        </audio>
        """
        
        # Display audio player
        st.markdown(audio_html, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error playing audio: {e}")
