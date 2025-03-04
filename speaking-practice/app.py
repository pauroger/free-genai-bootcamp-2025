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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("speaking_tutor")
logger.setLevel(logging.DEBUG)

# Create a file handler
log_file = Path("./app_debug.log")
file_handler = logging.FileHandler(str(log_file))
file_handler.setLevel(logging.DEBUG)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

# Set page config as the VERY FIRST Streamlit command
st.set_page_config(
    page_title="🗣️ Speaking Tutor",
    page_icon="🗣️",
    layout="wide",
)

# Main app layout
st.title("🗣️ Speaking Tutor")

apply_custom_theme(primary_color="#90cdec")

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
        Record yourself describing the image. When finished, click stop to save the recording.
    """)
    
    # Create directory for recordings if it doesn't exist
    recordings_dir = Path("./recordings")
    recordings_dir.mkdir(exist_ok=True)
    
    # Initialize session state for recording
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None
    
    # Function to generate a unique file name with timestamp
    def generate_filename():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(recordings_dir / f"{timestamp}_recording.mp3")
    
    # Recording controls
    audio_col1, audio_col2 = st.columns(2)
    
    with audio_col1:
        # Single recording button that toggles state
        button_label = "Stop Recording" if st.session_state.recording else "Start Recording"
        button_type = "primary" if st.session_state.recording else "secondary"
        
        if st.button(button_label, key="toggle_recording", type=button_type):
            if not st.session_state.recording:
                # Start recording
                logger.info("Starting recording")
                st.session_state.recording = True
                st.session_state.audio_file = generate_filename()
                
                # Create a new audio processor that reads the recording state from session_state
                st.session_state.audio_processor = AudioProcessor(
                    recording_state_accessor=lambda: st.session_state.recording
                )
                logger.info(f"Created new audio processor, recording to {st.session_state.audio_file}")
            else:
                # Stop recording
                logger.info("Stopping recording")
                st.session_state.recording = False
                
                # If we have an audio processor with data, save the audio
                if hasattr(st.session_state, 'audio_processor') and st.session_state.audio_processor.has_audio():
                    try:
                        # Log info about audio chunks
                        chunks_count = st.session_state.audio_processor.get_chunks_count()
                        logger.info(f"Found {chunks_count} audio chunks to save")
                        st.sidebar.write(f"Found {chunks_count} audio chunks to save")
                        
                        # Ensure the directory exists
                        os.makedirs(os.path.dirname(st.session_state.audio_file), exist_ok=True)
                        logger.info(f"Ensuring directory exists: {os.path.dirname(st.session_state.audio_file)}")
                        
                        # Save the audio
                        save_result = st.session_state.audio_processor.save_audio(st.session_state.audio_file)
                        
                        if save_result:
                            # Verify file was created
                            if os.path.exists(st.session_state.audio_file):
                                file_size = os.path.getsize(st.session_state.audio_file)
                                logger.info(f"File saved successfully: {file_size} bytes")
                                st.sidebar.write(f"File saved: {file_size} bytes")
                                st.success(f"Recording saved to {st.session_state.audio_file}")
                            else:
                                logger.error(f"File was not created: {st.session_state.audio_file}")
                                st.sidebar.error(f"File was not created")
                                st.error("Failed to save recording")
                        else:
                            logger.error("Failed to save audio")
                            st.error("Failed to save recording")
                        
                        # Clear the audio processor
                        st.session_state.audio_processor.clear()
                    except Exception as e:
                        error_msg = f"Error saving audio: {str(e)}"
                        logger.error(error_msg)
                        logger.error(traceback.format_exc())
                        st.sidebar.error(error_msg)
                        st.error("Failed to save recording. See debug info for details.")
                else:
                    warning_msg = "No audio chunks to save"
                    logger.warning(warning_msg)
                    st.sidebar.warning(warning_msg)
            st.rerun()
    
    # Display recording state
    if st.session_state.recording:
        with audio_col2:
            st.markdown("🔴 **Recording in progress...**")
    
    # WebRTC streamer for audio with custom UI
    webrtc_ctx = webrtc_streamer(
        key="audio-recorder",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=256,
        media_stream_constraints={"video": False, "audio": True},
        async_processing=True,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        in_recorder_factory=None,  # Disable the default START button
        video_html_attrs={"style": {"display": "none"}},  # Hide video UI
        audio_processor_factory=lambda: st.session_state.audio_processor if hasattr(st.session_state, 'audio_processor') else None
    )

    # Logging for debugging
    st.sidebar.markdown("### Debug Info")
    st.sidebar.write(f"WebRTC State: {webrtc_ctx.state}")
    st.sidebar.write(f"Recording: {st.session_state.recording}")
    
    # Display previously recorded audio if available
    if not st.session_state.recording and st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
        st.markdown("### Last Recording")
        with open(st.session_state.audio_file, "rb") as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")
            
            # Provide download button for the recorded audio
            st.download_button(
                label="Download Recording",
                data=audio_bytes,
                file_name=os.path.basename(st.session_state.audio_file),
                mime="audio/mp3"
            )

# Add the requirements note
st.sidebar.markdown("### Requirements")
st.sidebar.code("""
pip install streamlit-webrtc
pip install av
pip install pydub
pip install numpy
""")

# Add footer
st.markdown("---")
st.markdown("© Speaking Tutor - Practice your speaking skills with AI-generated prompts")