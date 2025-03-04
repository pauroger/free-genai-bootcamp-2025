import streamlit as st
import base64
from datetime import datetime
import os
from pathlib import Path

# Create recordings directory
recordings_dir = Path("./recordings")
recordings_dir.mkdir(exist_ok=True)

st.title("Audio Recorder")

# Session state for recording
if "recorded_audio" not in st.session_state:
    st.session_state.recorded_audio = None

# JavaScript to handle recording
st.markdown("""
    <script type="text/javascript">
        const startRecording = () => {
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'inline-block';
            document.getElementById('status').innerText = 'Recording...';
        }
        
        const stopRecording = () => {
            document.getElementById('startBtn').style.display = 'inline-block';
            document.getElementById('stopBtn').style.display = 'none';
            document.getElementById('status').innerText = 'Recording stopped';
        }
    </script>
""", unsafe_allow_html=True)

# HTML for audio recording
audio_recorder_html = """
<style>
    .button {
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
        margin: 5px;
    }
    .start {background-color: #4CAF50; color: white;}
    .stop {background-color: #f44336; color: white; display: none;}
    .status {margin-top: 10px; font-style: italic;}
    .audio-container {margin-top: 15px;}
</style>

<div>
    <button id="startBtn" class="button start" onclick="startRecording()">Start Recording</button>
    <button id="stopBtn" class="button stop" onclick="stopRecording()">Stop Recording</button>
    <p id="status" class="status">Click Start to begin recording</p>
    <div class="audio-container">
        <audio id="audioPlayback" controls style="display:none;"></audio>
    </div>
</div>

<script>
    let mediaRecorder;
    let audioChunks = [];
    
    document.getElementById('startBtn').addEventListener('click', async () => {
        audioChunks = [];
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            
            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    audioChunks.push(e.data);
                }
            };
            
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = document.getElementById('audioPlayback');
                audio.src = audioUrl;
                audio.style.display = 'block';
                
                // Convert to base64 and send to Python
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = () => {
                    const base64data = reader.result.split(',')[1];
                    
                    // Use window.parent.postMessage to communicate with Streamlit
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: base64data
                    }, '*');
                };
                
                // Stop tracks
                stream.getTracks().forEach(track => track.stop());
            };
            
            mediaRecorder.start();
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'inline-block';
            document.getElementById('status').innerText = 'Recording... Speak now';
        } catch (err) {
            console.error('Error accessing microphone:', err);
            document.getElementById('status').innerText = 'Error: ' + err.message;
        }
    });
    
    document.getElementById('stopBtn').addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            document.getElementById('startBtn').style.display = 'inline-block';
            document.getElementById('stopBtn').style.display = 'none';
            document.getElementById('status').innerText = 'Recording stopped. Press play to hear.';
        }
    });
</script>
"""

# Use the custom component
audio_data = st.components.v1.html(audio_recorder_html, height=240)

# If we receive data from the component
if audio_data is not None and isinstance(audio_data, str):
    # Save the base64 data to session state
    st.session_state.recorded_audio = audio_data

# Process audio if available in session state
if st.session_state.recorded_audio:
    try:
        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = str(recordings_dir / f"{timestamp}_recording.webm")
        
        # Convert base64 to binary and save
        binary_data = base64.b64decode(st.session_state.recorded_audio)
        with open(file_path, "wb") as f:
            f.write(binary_data)
        
        # Display success message
        st.success(f"Audio saved to {file_path}")
        
        # Display audio
        st.audio(binary_data, format="audio/webm")
        
        # Add download button
        st.download_button(
            label="Download Recording",
            data=binary_data,
            file_name=f"{timestamp}_recording.webm",
            mime="audio/webm"
        )
        
        # Clear the session state after successful processing
        st.session_state.recorded_audio = None
        
    except Exception as e:
        st.error(f"Error saving audio: {str(e)}")