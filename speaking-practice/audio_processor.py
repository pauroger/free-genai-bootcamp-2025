import logging
import traceback
import pydub
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audio_processor")
logger.setLevel(logging.DEBUG)

# Create a file handler
log_file = Path("./audio_debug.log")
file_handler = logging.FileHandler(str(log_file))
file_handler.setLevel(logging.DEBUG)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(file_handler)

class AudioProcessor:
    def __init__(self, recording_state_accessor):
        """
        Initialize the audio processor
        
        Parameters:
        recording_state_accessor - A function that returns True when recording is active
        """
        self.audio_chunks = []
        self.recording_state = "STOPPED"
        self.sample_rate = 16000
        self._get_recording_state = recording_state_accessor
        logger.info("AudioProcessor initialized")
    
    def recv(self, frame):
        if self._get_recording_state():
            try:
                logger.debug(f"Received frame: format={frame.format}, sample_rate={frame.sample_rate}, layout={frame.layout.channels}")
                
                # Convert to numpy array and check for valid data
                ndarray = frame.to_ndarray()
                if ndarray.size == 0:
                    logger.warning("Empty frame received")
                    return frame
                
                logger.debug(f"Frame shape: {ndarray.shape}, dtype: {ndarray.dtype}, min: {ndarray.min()}, max: {ndarray.max()}")
                
                sound = pydub.AudioSegment(
                    data=ndarray.tobytes(),
                    sample_width=frame.format.bytes,
                    frame_rate=frame.sample_rate,
                    channels=len(frame.layout.channels)
                )
                
                self.audio_chunks.append(sound)
                logger.info(f"Added audio chunk #{len(self.audio_chunks)}, duration: {sound.duration_seconds:.2f}s")
                
            except Exception as e:
                logger.error(f"Error in recv: {str(e)}")
                logger.error(traceback.format_exc())
        return frame
    
    def get_chunks_count(self):
        """Returns the number of audio chunks collected"""
        return len(self.audio_chunks)
    
    def has_audio(self):
        """Returns True if there are audio chunks collected"""
        return len(self.audio_chunks) > 0
    
    def get_combined_audio(self):
        """Combines all audio chunks and returns a single AudioSegment"""
        if not self.audio_chunks:
            logger.warning("No audio chunks to combine")
            return None
        
        logger.info(f"Combining {len(self.audio_chunks)} audio chunks")
        try:
            combined = sum(self.audio_chunks, pydub.AudioSegment.empty())
            logger.info(f"Combined audio: duration={combined.duration_seconds:.2f}s, channels={combined.channels}")
            return combined
        except Exception as e:
            logger.error(f"Error combining audio chunks: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def save_audio(self, filepath, format="mp3"):
        """
        Save the combined audio to a file
        
        Parameters:
        filepath - Path where to save the audio file
        format - Format to save the audio in (default: mp3)
        
        Returns:
        bool - True if saved successfully, False otherwise
        """
        combined = self.get_combined_audio()
        if not combined:
            return False
        
        try:
            logger.info(f"Saving audio to {filepath}")
            combined.export(filepath, format=format)
            logger.info(f"Audio saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving audio: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def clear(self):
        """Clear all audio chunks"""
        logger.info(f"Clearing {len(self.audio_chunks)} audio chunks")
        self.audio_chunks = []