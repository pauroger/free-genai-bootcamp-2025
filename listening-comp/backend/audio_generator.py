import boto3
import json
import os
import wave
import struct
from typing import Dict, List, Tuple
import tempfile
from datetime import datetime
from pydub import AudioSegment

# MODEL_ID = "huggingface-asr-whisper-large-v3-turbo"
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

class AudioGenerator:
    def __init__(self):
        # self.bedrock = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.bedrock = boto3.client('bedrock-runtime', region_name="eu-west-1")
        self.polly = boto3.client('polly')
        self.model_id = MODEL_ID
        
        # Define English and German neural voices by language and gender
        self.voices = {
            'en-US': {
                'male': 'Matthew', 'female': 'Joanna', 'announcer': 'Stephen'
            },
            'de-DE': {
                'male': 'Hans', 'female': 'Marlene', 'announcer': 'Vicki'
            }
        }


        # Default language code
        self.language_code = 'en-US'
        
        # Create audio output directory
        self.audio_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "frontend/static/audio"
        )
        os.makedirs(self.audio_dir, exist_ok=True)

    def _invoke_bedrock(self, prompt: str) -> str:
        """Invoke Bedrock with the given prompt using converse API"""
        messages = [{
            "role": "user",
            "content": [{
                "text": prompt
            }]
        }]
        
        try:
            response = self.bedrock.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={
                    "temperature": 0.3,
                    "topP": 0.95,
                    "maxTokens": 2000
                }
            )
            return response['output']['message']['content'][0]['text']
        except Exception as e:
            print(f"Error in Bedrock converse: {str(e)}")
            raise e

    def validate_conversation_parts(self, parts: List[Tuple[str, str, str]]) -> bool:
        """
        Validate that the conversation parts are properly formatted. Returns
        True if valid, False otherwise.
        """
        if not parts:
            print("Error: No conversation parts generated")
            return False
            
        # Check that we have an announcer for intro
        if not parts[0][0].lower() == 'announcer':
            print("Error: First speaker must be Announcer")
            return False
            
        # Check that each part has valid content
        for i, (speaker, text, gender) in enumerate(parts):
            if not speaker or not isinstance(speaker, str):
                print(f"Error: Invalid speaker in part {i+1}")
                return False
            if not text or not isinstance(text, str):
                print(f"Error: Invalid text in part {i+1}")
                return False
            if gender not in ['male', 'female']:
                print(f"Error: Invalid gender in part {i+1}: {gender}")
                return False
                
        return True

    def parse_conversation(self, question: Dict) -> List[Tuple[str, str, str]]:
        """
        Convert question into a format for audio generation.
        Returns a list of (speaker, text, gender) tuples.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                prompt = f"""
                You are a listening test audio script generator for English and German.
                Format the following question for audio generation.
                
                Rules:
                1. Introduction and Question parts:
                   - Must start with 'Speaker: Announcer (Gender: male)'
                   - Keep as separate parts.
                
                2. Conversation parts:
                   - Name speakers based on their role (e.g., Student, Teacher).
                   - Must specify gender EXACTLY as either 'Gender: male' or 'Gender: female'.
                   - Use consistent names for the same speaker.
                   - Split long speeches at natural pauses.
                
                Format each part EXACTLY like this, with no variations:
                Speaker: [name] (Gender: male)
                Text: [English or German text]
                ---
                
                Example format:
                Speaker: Announcer (Gender: male)
                Text: Please listen to the following conversation and answer the question.
                ---
                Speaker: Student (Gender: female)
                Text: Excuse me, does this train stop at the main station?
                ---
                
                Question to format:
                {json.dumps(question, ensure_ascii=False, indent=2)}
                
                Output ONLY the formatted parts in order: introduction, conversation, question.
                Make sure to specify gender EXACTLY as shown in the example.
                """
                
                response = self._invoke_bedrock(prompt)
                
                parts = []
                current_speaker = None
                current_gender = None
                current_text = None
                speaker_genders = {}
                
                for line in response.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('Speaker:'):
                        if current_speaker and current_text:
                            parts.append((current_speaker, current_text, current_gender))
                        try:
                            speaker_part = line.split('Speaker:')[1].strip()
                            current_speaker = speaker_part.split('(')[0].strip()
                            gender_part = speaker_part.split('Gender:')[1].split(')')[0].strip().lower()
                            
                            if 'male' in gender_part:
                                current_gender = 'male'
                            elif 'female' in gender_part:
                                current_gender = 'female'
                            else:
                                raise ValueError(f"Invalid gender format: {gender_part}")
                            
                            if current_speaker.lower() in ['female', 'woman', 'girl', 'lady']:
                                current_gender = 'female'
                            elif current_speaker.lower() in ['male', 'man', 'boy']:
                                current_gender = 'male'
                            
                            if current_speaker in speaker_genders:
                                if current_gender != speaker_genders[current_speaker]:
                                    print(f"Warning: Gender mismatch for {current_speaker}. Using previously assigned gender {speaker_genders[current_speaker]}")
                                current_gender = speaker_genders[current_speaker]
                            else:
                                speaker_genders[current_speaker] = current_gender
                        except Exception as e:
                            print(f"Error parsing speaker/gender: {line}")
                            raise e
                    elif line.startswith('Text:'):
                        current_text = line.split('Text:')[1].strip()
                    elif line == '---' and current_speaker and current_text:
                        parts.append((current_speaker, current_text, current_gender))
                        current_speaker = None
                        current_gender = None
                        current_text = None
                        
                if current_speaker and current_text:
                    parts.append((current_speaker, current_text, current_gender))
                
                if self.validate_conversation_parts(parts):
                    return parts
                    
                print(f"Attempt {attempt + 1}: Invalid conversation format, retrying...")
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception("Failed to parse conversation after multiple attempts")
        
        raise Exception("Failed to generate valid conversation format")

    def get_voice_for_gender(self, speaker: str, gender: str, language_code: str = None) -> str:
        """Get an appropriate voice for the given speaker, gender, and language"""
        lang = language_code if language_code else self.language_code
        if speaker.lower() == 'announcer':
            return self.voices[lang]['announcer']
        elif gender == 'male':
            return self.voices[lang]['male']
        else:
            return self.voices[lang]['female']

    def generate_audio_part(self, text: str, voice_name: str, language_code: str) -> str:
        """Generate audio for a single part using Amazon Polly"""
        # Use neural for English; for German, use standard since that's what these voices support.
        engine = "neural"
        if language_code == "de-DE":
            engine = "standard"
        response = self.polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_name,
            Engine=engine,
            LanguageCode=language_code
        )
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(response['AudioStream'].read())
            return temp_file.name

    # def combine_audio_files(self, audio_files: List[str], output_file: str) -> bool:
    #     """Combine multiple MP3 audio files by concatenating their binary data."""
    #     try:
    #         with open(output_file, 'wb') as wfd:
    #             for audio_file in audio_files:
    #                 with open(audio_file, 'rb') as fd:
    #                     # Read the entire file and write it to the output file.
    #                     data = fd.read()
    #                     wfd.write(data)
    #         return True
    #     except Exception as e:
    #         print(f"Error combining audio files: {str(e)}")
    #         if os.path.exists(output_file):
    #             os.unlink(output_file)
    #         return False
    #     finally:
    #         # Clean up the temporary audio parts
    #         for audio_file in audio_files:
    #             if os.path.exists(audio_file):
    #                 try:
    #                     os.unlink(audio_file)
    #                 except Exception as e:
    #                     print(f"Error cleaning up {audio_file}: {str(e)}")

    def combine_audio_files(self, audio_files: List[str], output_file: str) -> bool:
        try:
            combined = AudioSegment.empty()
            for file in audio_files:
                segment = AudioSegment.from_mp3(file)
                combined += segment
            combined.export(output_file, format="mp3")
            return True
        except Exception as e:
            print(f"Error combining audio files: {str(e)}")
            return False

    def generate_silence(self, duration_ms: int) -> str:
        """Generate a silent MP3 file for the specified duration."""
        output_file = os.path.join(self.audio_dir, f'silence_{duration_ms}ms.mp3')
        silence = AudioSegment.silent(duration=duration_ms)
        silence.export(output_file, format="mp3", bitrate="64k")
        return output_file

    def generate_audio(self, question: Dict, language_code: str = 'en-US') -> str:
        """
        Generate audio for the entire question.
        Returns the path to the generated audio file.
        """
        self.language_code = language_code
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.audio_dir, f"question_{timestamp}.mp3")
        
        try:
            parts = self.parse_conversation(question)
            audio_parts = []
            
            # Pre-generate pauses
            long_pause = self.generate_silence(3000)
            short_pause = self.generate_silence(1000)
            
            for i, (speaker, text, gender) in enumerate(parts):
                # Check if this announcer part indicates a transition
                if speaker.lower() == 'announcer' or speaker.lower() == 'introduction':
                    # If the text indicates the start of the question
                    if "?" in text or "frage:" in text.lower() or "question:" in text.lower():
                        # Insert a pause before this question if previous parts exist
                        if audio_parts:
                            audio_parts.append(long_pause)
                    # If the text indicates options (e.g., begins with "Option" or "Optionen")
                    elif text.lower().startswith("option") or "optionen" in text.lower() or "conversation" in text.lower():
                        # Insert a longer pause before the options
                        audio_parts.append(long_pause)
                
                # Generate the audio for the current part
                voice = self.get_voice_for_gender(speaker, gender, language_code)
                print(f"Using voice {voice} for {speaker} ({gender})")
                audio_file = self.generate_audio_part(text, voice, language_code)
                if not audio_file:
                    raise Exception("Failed to generate audio part")
                audio_parts.append(audio_file)
                
                # Add a short pause between parts, if not the last part
                if i < len(parts) - 1:
                    audio_parts.append(short_pause)
            
            if not self.combine_audio_files(audio_parts, output_file):
                raise Exception("Failed to combine audio files")
            
            return output_file
            
        except Exception as e:
            if os.path.exists(output_file):
                os.unlink(output_file)
            raise Exception(f"Audio generation failed: {str(e)}")
