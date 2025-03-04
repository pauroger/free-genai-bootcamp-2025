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
from audio_processor import AudioProcessor

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
    page_title="🗣️ Speaking Tutor",
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
    
    st.subheader("Step 2: Practice Speaking")
    st.markdown("""
    1. Click the **START** button to begin recording ⭐
    2. Describe the image you see in detail
    3. Click **STOP** when you're done
    4. Listen to your recording by clicking play
    5. Repeat as many times as you want to practice!
    """)
    
    st.subheader("Tips for Better Practice")
    st.markdown("""
    - Try describing what you see in complete sentences
    - Imagine you're explaining the image to someone who can't see it
    - Practice using varied vocabulary and descriptive language
    - You can record as many times as you want to improve
    """)
    
    # Debug Info (collapsed by default)
    with st.expander("Debug Info", expanded=False):
        if 'webrtc_ctx' in st.session_state:
            st.write(f"WebRTC State: {st.session_state.webrtc_ctx.state}")
        st.write(f"Recording: {st.session_state.get('recording', False)}")
        st.write(f"Number of saved recordings: {len(st.session_state.get('recordings', []))}")

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

# SECTION 2: AUDIO RECORDING (RIGHT SIDE)
with right_section:
    st.header("2 - Practice Speaking")
    
    st.markdown("""
        Record yourself describing the image. Use the START/STOP buttons to control recording.
    """)
    
    # Create directory for recordings if it doesn't exist
    recordings_dir = Path("./recordings")
    recordings_dir.mkdir(exist_ok=True)
    
    # Manual recording interface
    st.write("### Manual Recording:")
    manual_record = st.button("START", key="manual_record", type="primary")
    manual_stop = st.button("STOP", key="manual_stop", type="secondary")
    
    if manual_record:
        st.session_state.recording = True
        st.session_state.current_audio_file = generate_filename()
        st.session_state.audio_chunks = []
        st.session_state.recording_start_time = time.time()
        st.rerun()
        
    if manual_stop and st.session_state.get('recording', False):
        st.session_state.recording = False
        duration = time.time() - st.session_state.get('recording_start_time', time.time())
        
        # Create a recording
        try:
            # Create a silent audio segment for demo purposes
            # In a real app, you would use actual recorded audio here
            silent_audio = pydub.AudioSegment.silent(duration=int(duration * 1000))
            
            # Save this recording
            os.makedirs(os.path.dirname(st.session_state.current_audio_file), exist_ok=True)
            silent_audio.export(st.session_state.current_audio_file, format="mp3")
            
            # Add to recordings list
            if 'recordings' not in st.session_state:
                st.session_state.recordings = []
            
            st.session_state.recordings.append({
                "path": st.session_state.current_audio_file,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "duration": f"{duration:.1f}s",
                "size": os.path.getsize(st.session_state.current_audio_file)
            })
            st.success("Recording saved!")
            st.rerun()
        except Exception as e:
            st.error(f"Error creating recording: {e}")
    
    # Show recording status
    if st.session_state.get('recording', False):
        st.markdown("🔴 **Recording in progress...**")
        duration = time.time() - st.session_state.get('recording_start_time', time.time())
        st.write(f"Recording duration: {duration:.1f} seconds")
        st.info("Describe the image you see. Click 'STOP' when finished.")
    
    # Display all recordings with playback and download options
    if st.session_state.recordings:
        st.markdown("### Your Recordings")
        
        for idx, recording in enumerate(st.session_state.recordings):
            with st.expander(f"Recording {idx+1} - {recording['timestamp']} ({recording['duration']})", expanded=(idx == len(st.session_state.recordings)-1)):
                if os.path.exists(recording['path']):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        with open(recording['path'], "rb") as audio_file:
                            audio_bytes = audio_file.read()
                            st.audio(audio_bytes, format="audio/mp3")
                    
                    with col2:
                        with open(recording['path'], "rb") as audio_file:
                            st.download_button(
                                label="Download",
                                data=audio_file,
                                file_name=os.path.basename(recording['path']),
                                mime="audio/mp3",
                                key=f"download_{idx}"
                            )
                else:
                    st.warning(f"Recording file not found: {recording['path']}")
    else:
        st.info("No recordings yet. Click 'START' to begin!")

# Add footer
st.markdown("---")
st.markdown("© Speaking Tutor - Practice your speaking skills with AI-generated prompts")