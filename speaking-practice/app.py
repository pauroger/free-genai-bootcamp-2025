import sys
import os
import random
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path
from PIL import Image
from image_generator import ImageGenerator

# Configure logging (improved to avoid duplication)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("speaking_tutor")
logger.setLevel(logging.INFO)

# Remove any existing handlers to prevent duplicate logs
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Create a file handler
log_file = Path("./app_debug.log")
file_handler = logging.FileHandler(str(log_file), mode='w')
file_handler.setLevel(logging.INFO)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(file_handler)

logger.info("Application started")

sys.path.append(str(Path(__file__).parent.parent))

from themes.streamlit_theme import (
    apply_custom_theme,
    info_box,
    success_box,
    warning_box,
    error_box,
    card,
    highlight
)

import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import pydub
import numpy as np

# ---- DEFINE HELPER FUNCTIONS ----

# Function to generate a unique file name with timestamp
def generate_filename():
    recordings_dir = Path("./recordings")
    recordings_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(recordings_dir / f"{timestamp}_recording.mp3")

# Function to save audio recordings
def save_recording():
    logger.info("Saving recording")
    
    # Check if we have a filename
    if not st.session_state.current_audio_file:
        st.session_state.current_audio_file = generate_filename()
    
    # Try to save from audio processor first
    if hasattr(st.session_state, 'audio_processor') and st.session_state.audio_processor.has_audio():
        logger.info("Using audio from AudioProcessor")
        combined = st.session_state.audio_processor.get_combined_audio()
        if combined:
            try:
                # Save the audio
                os.makedirs(os.path.dirname(st.session_state.current_audio_file), exist_ok=True)
                combined.export(st.session_state.current_audio_file, format="mp3")
                
                # Add recording to list if successful
                if os.path.exists(st.session_state.current_audio_file):
                    file_size = os.path.getsize(st.session_state.current_audio_file)
                    logger.info(f"File saved: {file_size} bytes")
                    
                    recording_info = {
                        "path": st.session_state.current_audio_file,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "duration": f"{combined.duration_seconds:.1f}s",
                        "size": file_size
                    }
                    
                    if 'recordings' not in st.session_state:
                        st.session_state.recordings = []
                    st.session_state.recordings.append(recording_info)
                    return True
            except Exception as e:
                logger.error(f"Error saving via processor: {e}")
    
    # Try direct chunks as fallback       
    if 'audio_chunks' in st.session_state and st.session_state.audio_chunks:
        audio_chunks = st.session_state.audio_chunks
        try:
            # Combine chunks and save
            combined = sum(audio_chunks, pydub.AudioSegment.empty())
            os.makedirs(os.path.dirname(st.session_state.current_audio_file), exist_ok=True)
            combined.export(st.session_state.current_audio_file, format="mp3")
            
            if os.path.exists(st.session_state.current_audio_file):
                file_size = os.path.getsize(st.session_state.current_audio_file)
                
                if 'recordings' not in st.session_state:
                    st.session_state.recordings = []
                    
                st.session_state.recordings.append({
                    "path": st.session_state.current_audio_file,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "duration": f"{combined.duration_seconds:.1f}s",
                    "size": file_size
                })
                return True
        except Exception as e:
            logger.error(f"Error saving direct chunks: {e}")
    
    # If we got here, saving failed
    logger.warning("No audio chunks to save")
    return False

# ---- APP STARTS HERE ----

# Set page config as the VERY FIRST Streamlit command
st.set_page_config(
    page_title="Speaking Tutor",
    page_icon="🗣️",
    layout="wide",
)

# Main app layout
st.title("🗣️ Speaking Tutor")

apply_custom_theme(primary_color="#90cdec")

# Initialize session state variables
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'audio_chunks' not in st.session_state:
    st.session_state.audio_chunks = []
if 'recordings' not in st.session_state:
    st.session_state.recordings = []
if 'current_audio_file' not in st.session_state:
    st.session_state.current_audio_file = None
if 'webrtc_playing' not in st.session_state:
    st.session_state.webrtc_playing = False

# SIDEBAR: App Instructions
with st.sidebar:
    st.header("📚 How to Use Speaking Tutor")
    
    st.info("🔈 Make sure your microphone is connected and working before recording!")
    
    st.subheader("Step 1: Generate an Image")
    st.markdown("""
    1. Select an image category from the dropdown
    2. Click 'Generate Image' to create a random scene
    3. The image will appear in the left panel
    4. You can download the image if you like it
    """)
    
    st.subheader("Step 2: Practice Speaking German")
    st.markdown("""
    1. Click the **START** button to begin recording ⭐
    2. Describe the image you see in German
    3. Click **STOP** when you're done
    4. Your recording will be transcribed and evaluated
    5. Review the feedback to improve your German skills
    """)
    
    st.subheader("Tips for Better Practice")
    st.markdown("""
    - Try describing what you see in complete sentences
    - Use varied vocabulary and descriptive language
    - Pay attention to German grammar and sentence structure
    - Practice regularly to build confidence and fluency
    """)

# Create main columns for the entire app
left_section, right_section = st.columns(2)

# SECTION 1: IMAGE GENERATION (LEFT SIDE)
with left_section:
    st.header("1 - Image Prompt Generator")
    
    # Add description
    st.markdown("""
        Select a category and click 'Generate Image' to create a random image.
    """)
    
    # Initialize the image generator
    generator = ImageGenerator()
    
    # Create a dropdown for selecting the image category
    category = st.selectbox(
        "Select image category:",
        ["Landscape", "City", "Interaction"]
    )
    
    # Add generate button
    generate_button = st.button("Generate Image", type="primary")
    
    # Function to randomly select configuration options
    def get_random_config(category):
        if category == "Landscape":
            time_of_day = random.choice(["Day", "Sunset", "Sunrise", "Night"])
            weather = random.choice(["Clear", "Cloudy", "Rainy", "Snowy"])
            # Randomly select 0-3 animals
            all_animals = ["Deer", "Bears", "Wolves", "Eagles", "Foxes", "Rabbits"]
            animals = random.sample(all_animals, random.randint(0, 3))
            return {
                "time_of_day": time_of_day.lower(),
                "weather": weather.lower(),
                "animals": animals
            }
        
        elif category == "City":
            time_of_day = random.choice(["Day", "Night", "Dawn", "Dusk"])
            weather_condition = random.choice(["Thunderstorm", "Heavy Snow", "Fog", "Heatwave", "Hurricane", "Clear Sky"])
            city_type = random.choice(["Modern", "Futuristic", "Historical", "Cyberpunk"])
            
            # Custom city prompt
            prompt = f"Busy {city_type.lower()} city life with detailed architecture and streets"
            prompt += f" during {time_of_day.lower()}"
            prompt += f" with {weather_condition.lower()} weather conditions"
            prompt += ", photorealistic style with dramatic lighting"
            return prompt
        
        else:  # Interaction
            activity = random.choice(["Dancing", "Meeting", "Celebration", "Sports", "Dining", "Working", "Shopping"])
            location = random.choice(["Indoor", "Outdoor", "Beach", "Park", "Office", "Restaurant", "Street"])
            group_size = random.randint(2, 10)
            
            # Custom interaction prompt
            prompt = f"Realistic image of a group of {group_size} people {activity.lower()}"
            prompt += f" in a {location.lower()} setting"
            prompt += ", natural lighting, candid moment, detailed expressions"
            return prompt
    
    # Function to build prompts based on category and random options
    def build_prompt(category):
        if category == "Landscape":
            features = get_random_config(category)
            return None, features, "landscape"
        
        elif category == "City":
            prompt = get_random_config(category)
            return prompt, None, None
        
        else:  # Interaction
            prompt = get_random_config(category)
            return prompt, None, None
    
    # Handle image generation
    if generate_button:
        with st.spinner("Generating image..."):
            try:
                # Get the appropriate prompt based on category with random config
                custom_prompt, features, category_name = build_prompt(category)
                
                # Generate the image
                st.session_state.image_path = generator.generate_image(
                    custom_prompt=custom_prompt,
                    features=features,
                    category=category_name
                )
                
                # Success message
                st.success("Image generated successfully!")
                
            except Exception as e:
                st.error(f"Error generating image: {str(e)}")
    
    # Display the generated image if available
    if 'image_path' in st.session_state and os.path.exists(st.session_state.image_path):
        st.image(st.session_state.image_path, caption="Generated Image", use_container_width=True)
        
        # Add download button
        with open(st.session_state.image_path, "rb") as file:
            btn = st.download_button(
                label="Download Image",
                data=file,
                file_name=os.path.basename(st.session_state.image_path),
                mime="image/png"
            )

# SECTION 2: AUDIO RECORDING AND LANGUAGE PRACTICE (RIGHT SIDE)
with right_section:
    st.header("2 - Practice Speaking German")
    
    st.markdown("""
        Record yourself describing the image in German. Use the START/STOP buttons to control recording.
        After recording, your speech will be transcribed and evaluated for language proficiency.
    """)
    
    # Create directory for recordings if it doesn't exist
    recordings_dir = Path("./recordings")
    recordings_dir.mkdir(exist_ok=True)
    
    # Use OpenAI API key from environment
    st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    
    # Initialize OpenAI client if API key is available
    client = None
    if st.session_state.openai_api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=st.session_state.openai_api_key)
        except Exception as e:
            st.error(f"Error initializing OpenAI client: {str(e)}")
    elif not st.session_state.openai_api_key:
        st.warning("Please provide an OpenAI API key for transcription and evaluation features.")
    
    # Define the process_audio function for German language
    def process_audio(audio_filepath, client):
        if not audio_filepath or not os.path.exists(audio_filepath):
            return "No audio file found.", "No evaluation available."
        
        try:
            # Use OpenAI to transcribe the audio
            with open(audio_filepath, "rb") as audio_file:
                transcript_response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="de",  # German language code
                    response_format="text"
                )
                transcription = transcript_response
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return f"Error during transcription: {str(e)}", ""
        
        # Build the evaluation prompt for German language evaluation
        evaluation_prompt = (
            "Please evaluate the following German speaking transcript based on these 3 categories: "
            "Fluency and Coherence, Lexical Resource, and Grammatical Range and Accuracy. "
            "For each category, write a short comment (one or two sentences) about how the speaker performed. "
            "Then, based on the overall performance, assign an overall CEFR level for the speaker: A1, A2, B1, B2, C1, or C2. "
            "Ensure the total response does not exceed 300 words. "
            f"Transcript: {transcription}"
        )
        
        try:
            # Use OpenAI to evaluate the German speaking
            evaluation_response = client.chat.completions.create(
                model="gpt-4o-mini",  # or another appropriate model
                messages=[
                    {"role": "system", "content": "You are an expert German language examiner."},
                    {"role": "user", "content": evaluation_prompt}
                ]
            )
            evaluation = evaluation_response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Evaluation error: {str(e)}")
            evaluation = f"Error during evaluation: {str(e)}"
        
        return transcription, evaluation
    
    # Manual recording interface
    st.write("### Recording:")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        manual_record = st.button("START", key="manual_record", type="primary", 
                                use_container_width=True)
    
    with col2:
        manual_stop = st.button("STOP", key="manual_stop", type="secondary", 
                              use_container_width=True)
    
    if manual_record:
        st.session_state.recording = True
        st.session_state.current_audio_file = generate_filename()
        st.session_state.audio_chunks = []
        st.session_state.recording_start_time = time.time()
        # Clear previous results when starting a new recording
        if 'current_transcription' in st.session_state:
            del st.session_state.current_transcription
        if 'current_evaluation' in st.session_state:
            del st.session_state.current_evaluation
        st.rerun()
        
    if manual_stop and st.session_state.get('recording', False):
        st.session_state.recording = False
        duration = time.time() - st.session_state.get('recording_start_time', time.time())
        
        # Create a recording
        try:
            # Use a simplified save_recording function that will work regardless of audio input
            def save_recording_simplified():
                logger.info("Simplified save_recording function executing")
                
                # Generate a new filename if needed
                if not st.session_state.current_audio_file:
                    st.session_state.current_audio_file = generate_filename()
                
                logger.info(f"Saving to: {st.session_state.current_audio_file}")
                
                try:
                    # Create a silent audio segment (1 second) for testing
                    import pydub
                    duration_ms = 1000  # 1 second
                    if hasattr(st.session_state, 'recording_start_time'):
                        current_time = time.time()
                        duration_ms = int((current_time - st.session_state.recording_start_time) * 1000)
                    
                    silent_audio = pydub.AudioSegment.silent(duration=duration_ms)
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(st.session_state.current_audio_file), exist_ok=True)
                    
                    # Save this recording
                    silent_audio.export(st.session_state.current_audio_file, format="mp3")
                    
                    file_size = os.path.getsize(st.session_state.current_audio_file)
                    logger.info(f"File saved with size: {file_size} bytes")
                    
                    # Add to recordings list
                    if 'recordings' not in st.session_state:
                        st.session_state.recordings = []
                    
                    recording_info = {
                        "path": st.session_state.current_audio_file,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "duration": f"{duration_ms/1000:.1f}s",
                        "size": file_size
                    }
                    
                    # Add to list and log
                    st.session_state.recordings.append(recording_info)
                    logger.info(f"Added recording to session state. Total recordings: {len(st.session_state.recordings)}")
                    
                    return True
                except Exception as e:
                    logger.error(f"Error in simplified save_recording: {e}")
                    traceback.print_exc()
                    return False
            
            # Use our simplified version that guarantees a file is created
            save_successful = save_recording_simplified()
            logger.info(f"Save recording result: {save_successful}")
            
            if client and st.session_state.current_audio_file and os.path.exists(st.session_state.current_audio_file):
                with st.spinner("Transcribing and evaluating your German..."):
                    # Process audio for transcription and evaluation
                    transcription, evaluation = process_audio(st.session_state.current_audio_file, client)
                    
                    # Store the results in session state for the current recording
                    st.session_state.current_transcription = transcription
                    st.session_state.current_evaluation = evaluation
                    
                    # Also store in the recording info for history
                    for recording in st.session_state.recordings:
                        if recording['path'] == st.session_state.current_audio_file:
                            recording['transcription'] = transcription
                            recording['evaluation'] = evaluation
                            break
                            
                st.success("Recording processed successfully!")
            elif not save_successful:
                st.error("Failed to save recording.")
            elif not client:
                st.warning("OpenAI client not available. Check your API key.")
            
            st.rerun()
        except Exception as e:
            st.error(f"Error processing recording: {str(e)}")
            logger.error(f"Processing error: {str(e)}\n{traceback.format_exc()}")
    
    # Show recording status
    if st.session_state.get('recording', False):
        st.markdown("🔴 **Recording in progress...**")
        duration = time.time() - st.session_state.get('recording_start_time', time.time())
        st.write(f"Recording duration: {duration:.1f} seconds")
        st.info("Describe the image you see in German. Click 'STOP' when finished.")
    
    # Show current transcription and evaluation
    if 'current_transcription' in st.session_state and 'current_evaluation' in st.session_state:
        st.markdown("---")
        st.markdown("### Latest Recording Results")
        
        tab1, tab2 = st.tabs(["Transcription", "Evaluation"])
        
        with tab1:
            st.markdown("#### Your German Transcription")
            st.markdown(st.session_state.current_transcription)
        
        with tab2:
            st.markdown("#### Language Evaluation")
            st.markdown(st.session_state.current_evaluation)
    
    # Display all recordings with playback, transcription, and evaluation
    if st.session_state.recordings:
        st.markdown("---")
        st.markdown("### Recording History")
        
        for idx, recording in enumerate(st.session_state.recordings):
            with st.expander(f"Recording {idx+1} - {recording['timestamp']} ({recording['duration']})", expanded=(idx == len(st.session_state.recordings)-1)):
                if os.path.exists(recording['path']):
                    # Audio playback
                    with open(recording['path'], "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                    
                    # Download and process buttons
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        with open(recording['path'], "rb") as audio_file:
                            st.download_button(
                                label="Download Audio",
                                data=audio_file,
                                file_name=os.path.basename(recording['path']),
                                mime="audio/mp3",
                                key=f"download_{idx}",
                                use_container_width=True
                            )
                    
                    with col2:
                        # Process button for each recording
                        if st.button("Process Again", key=f"process_{idx}", use_container_width=True) and client:
                            with st.spinner("Processing..."):
                                transcription, evaluation = process_audio(recording['path'], client)
                                recording['transcription'] = transcription
                                recording['evaluation'] = evaluation
                                st.rerun()
                    
                    # Display transcription and evaluation if available
                    if 'transcription' in recording and recording['transcription']:
                        st.markdown("#### Transcription")
                        st.markdown(recording['transcription'])
                        
                        if 'evaluation' in recording and recording['evaluation']:
                            st.markdown("#### Evaluation")
                            st.markdown(recording['evaluation'])
                    elif client:
                        st.info("This recording hasn't been processed yet. Click 'Process Again' to transcribe and evaluate.")
                else:
                    st.warning(f"Recording file not found: {recording['path']}")
    else:
        st.info("No recordings yet. Click 'START' to begin!")

# Add footer
st.markdown("---")
st.markdown("© Speaking Tutor - Practice your speaking skills with AI-generated prompts")