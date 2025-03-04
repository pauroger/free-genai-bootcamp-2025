import streamlit as st
from datetime import datetime
import os
from pathlib import Path

# Install streamlit-audiorecorder if needed
# pip install streamlit-audiorecorder

try:
    from audiorecorder import audiorecorder
except ImportError:
    st.error("Please install the required package: pip install streamlit-audiorecorder")
    st.stop()

# Create recordings directory
recordings_dir = Path("./recordings")
recordings_dir.mkdir(exist_ok=True)

st.title("Audio Recorder")

# Create an instance of the audio recorder
recorder = audiorecorder("Click to record", "Recording... Click to stop")

# Get audio data
audio = recorder.recording()

# Check if audio data exists
if len(audio) > 0:
    # Create a unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = str(recordings_dir / f"{timestamp}_recording.wav")
    
    # Save the audio file
    audio.export(file_path, format="wav")
    
    # Success message
    st.success(f"Audio saved to {file_path}")
    
    # Display audio
    st.audio(audio.export().read())
    
    # Add a download button
    with open(file_path, "rb") as f:
        st.download_button(
            label="Download Recording",
            data=f,
            file_name=os.path.basename(file_path),
            mime="audio/wav"
        )