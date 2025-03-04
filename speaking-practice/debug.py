import streamlit as st
import base64
from datetime import datetime
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("audio_recorder_debug.log")
    ]
)

# Create recordings directory
recordings_dir = Path("./recordings")
recordings_dir.mkdir(exist_ok=True)
logging.info(f"Recordings directory: {recordings_dir.absolute()}")
logging.info(f"Directory exists: {recordings_dir.exists()}")
logging.info(f"Directory is writable: {os.access(str(recordings_dir.absolute()), os.W_OK)}")

st.title("Audio Recorder")

# Session state for recording
if "recorded_audio" not in st.session_state:
    st.session_state.recorded_audio = None
if "recording_stopped" not in st.session_state:
    st.session_state.recording_stopped = False

# HTML and JavaScript for audio recorder in single component
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
    .submit {background-color: #008CBA; color: white; display: none;}
    .status {margin-top: 10px; font-style: italic;}
    .audio-container {margin-top: 15px;}
</style>

<div>
    <button id="startBtn" class="button start" onclick="startRecording()">Start Recording</button>
    <button id="stopBtn" class="button stop" onclick="stopRecording()">Stop Recording</button>
    <button id="submitBtn" class="button submit" onclick="submitRecording()">Submit Recording</button>
    <p id="status" class="status">Click Start to begin recording</p>
    <div class="audio-container">
        <audio id="audioPlayback" controls style="display:none;"></audio>
    </div>
</div>

<script>
    let mediaRecorder;
    let audioChunks = [];
    window.latestAudioData = null;
    
    const startRecording = async () => {
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
                
                // Convert to base64 and store
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = () => {
                    const base64data = reader.result.split(',')[1];
                    console.log("Audio data captured, length:", base64data.length);
                    window.latestAudioData = base64data;
                    
                    // This important update fixes the core issue by making sure 
                    // Streamlit component state is updated with the audio data
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: { 
                            audio: base64data,
                            action: 'stop'
                        }
                    }, '*');
                    
                    // Add a delayed rerun to make sure Streamlit has the updated state
                    setTimeout(() => {
                        window.parent.postMessage({
                            type: 'streamlit:componentRerun',
                            value: {}
                        }, '*');
                    }, 100);
                };
                
                // Stop tracks
                stream.getTracks().forEach(track => track.stop());
            };
            
            mediaRecorder.start();
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'inline-block';
            document.getElementById('submitBtn').style.display = 'none';
            document.getElementById('status').innerText = 'Recording... Speak now';
        } catch (err) {
            console.error('Error accessing microphone:', err);
            document.getElementById('status').innerText = 'Error: ' + err.message;
        }
    };
    
    const stopRecording = () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            document.getElementById('startBtn').style.display = 'inline-block';
            document.getElementById('stopBtn').style.display = 'none';
            document.getElementById('submitBtn').style.display = 'inline-block';
            document.getElementById('status').innerText = 'Recording stopped. Press play to hear or submit to save.';
        }
    };
    
    const submitRecording = () => {
        if (window.latestAudioData) {
            console.log("Submitting audio data, length:", window.latestAudioData.length);
            try {
                // First store audio data in a variable to ensure it's correctly captured
                const audioToSubmit = window.latestAudioData;
                
                // Then send it to Streamlit
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: { 
                        audio: audioToSubmit,
                        action: 'submit'
                    }
                }, '*');
                
                console.log("Audio data sent to Streamlit");
                document.getElementById('status').innerText = 'Recording submitted';
                
                // Force a component rerun to ensure the data is processed
                setTimeout(() => {
                    window.parent.postMessage({
                        type: 'streamlit:componentRerun',
                        value: {}
                    }, '*');
                }, 100);
            } catch (err) {
                console.error("Error submitting audio:", err);
                document.getElementById('status').innerText = 'Error submitting: ' + err.message;
            }
        } else {
            console.warn("No audio data available to submit");
            document.getElementById('status').innerText = 'No recording available. Please record something first.';
        }
    };
</script>
"""

# Use the custom component
audio_data = st.components.v1.html(audio_recorder_html, height=240)

# If we receive data from the component
if audio_data is not None and isinstance(audio_data, dict):
    logging.info(f"Received audio_data with action: {audio_data.get('action')}")
    logging.info(f"Audio data present: {bool(audio_data.get('audio'))}")
    logging.info(f"Audio data length: {len(str(audio_data.get('audio', '')))}")
    
    if audio_data.get('action') == 'stop':
        # Just store the data but don't process yet
        st.session_state.recorded_audio = audio_data.get('audio')
        st.session_state.recording_stopped = True
        logging.info("Recording stopped - data stored in session state")
    elif audio_data.get('action') == 'submit' and audio_data.get('audio'):
        # User clicked Submit - process the audio
        logging.info("Submit action received with audio data")
        try:
            # Create a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = str(recordings_dir / f"{timestamp}_recording.webm")
            logging.info(f"Attempting to save to: {file_path}")
            
            # Convert base64 to binary and save
            try:
                logging.info("Starting base64 decoding")
                audio_base64 = audio_data.get('audio')
                logging.info(f"First 50 chars of base64: {audio_base64[:50] if audio_base64 else 'None'}")
                
                binary_data = base64.b64decode(audio_base64)
                logging.info(f"Base64 decode successful, got {len(binary_data)} bytes")
            except Exception as decode_error:
                logging.error(f"Base64 decode error: {str(decode_error)}")
                raise decode_error
                
            try:
                with open(file_path, "wb") as f:
                    f.write(binary_data)
                logging.info(f"File written successfully: {os.path.getsize(file_path)} bytes")
            except Exception as file_error:
                logging.error(f"File write error: {str(file_error)}")
                raise file_error
            
            # Display success message
            st.success(f"Audio saved to {file_path}")
            logging.info("Success message displayed")
            
            # Display audio
            st.audio(binary_data, format="audio/webm")
            logging.info("Audio player displayed")
            
            # Add download button
            st.download_button(
                label="Download Recording",
                data=binary_data,
                file_name=f"{timestamp}_recording.webm",
                mime="audio/webm"
            )
            logging.info("Download button added")
            
            # Reset the session state
            st.session_state.recorded_audio = None
            st.session_state.recording_stopped = False
            logging.info("Session state reset")
            
        except Exception as e:
            logging.error(f"Error saving audio: {str(e)}", exc_info=True)
            st.error(f"Error saving audio: {str(e)}")