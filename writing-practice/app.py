import streamlit as st
import requests
from enum import Enum
import json
from typing import Optional, List, Dict
import openai
import logging
import random

# Setup Custom Logging -----------------------
# Create a custom logger for your app only
logger = logging.getLogger('my_app')
logger.setLevel(logging.DEBUG)

# Remove any existing handlers to prevent duplicate logging
if logger.hasHandlers():
    logger.handlers.clear()

# Create file handler
fh = logging.FileHandler('app.log')
fh.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - MY_APP - %(message)s')
fh.setFormatter(formatter)

# Add handler to logger
logger.addHandler(fh)

# Prevent propagation to root logger
logger.propagate = False

# State Management
class AppState(Enum):
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"

class JapaneseLearningApp:
    def __init__(self):
        logger.debug("Initializing Japanese Learning App...")
        self.initialize_session_state()
        self.load_vocabulary()
        
    def initialize_session_state(self):
        """Initialize or get session state variables"""
        if 'app_state' not in st.session_state:
            st.session_state.app_state = AppState.SETUP
        if 'current_sentence' not in st.session_state:
            st.session_state.current_sentence = ""
        if 'review_data' not in st.session_state:
            st.session_state.review_data = None
            
    def load_vocabulary(self):
        """Fetch vocabulary from API using group_id from query parameters"""
        try:
            # Get group_id from query parameters
            group_id = st.query_params.get('group_id', '')
            
            if not group_id:
                st.error("No group_id provided in query parameters")
                self.vocabulary = None
                return
                
            # Make API request with the actual group_id
            url = f'http://localhost:5000/api/groups/{group_id}/words/raw'
            logger.debug(url)
            response = requests.get(url)
            logger.debug(f"Response status: {response.status_code}")
            
            # Check if response is successful and contains data
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.debug(f"Received data for group: {data.get('group_name', 'unknown')}") 
                    self.vocabulary = data
                except requests.exceptions.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    st.error(f"Invalid JSON response from API: {response.text}")
                    self.vocabulary = None
            else:
                logger.error(f"API request failed: {response.status_code}")
                st.error(f"API request failed with status code: {response.status_code}")
                self.vocabulary = None
        except Exception as e:
            logger.error(f"Failed to load vocabulary: {e}")
            st.error(f"Failed to load vocabulary: {str(e)}")
            self.vocabulary = None

    def generate_sentence(self, word: dict) -> str:
        """Generate a sentence using OpenAI API"""
        kanji = word.get('kanji', '')
        
        prompt = f"""Generate a simple Japanese sentence using the word '{kanji}'.
        The grammar should be scoped to JLPTN5 grammar.
        You can use the following vocabulary to construct a simple sentence:
        - simple objects eg. book, car, ramen, sushi
        - simple verbs, to drink, to eat, to meet
        - simple times eg. tomorrow, today, yesterday
        
        Please provide the response in this format:
        Japanese: [sentence in kanji/hiragana]
        English: [English translation]
        """
        
        logger.debug(f"Generating sentence for word: {kanji}")
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    def grade_submission(self, image) -> Dict:
        """Process image submission and grade it"""
        # TODO: Implement MangaOCR integration
        # For now, return mock data
        return {
            "transcription": "今日はラーメンを食べます",
            "translation": "I will eat ramen today",
            "grade": "S",
            "feedback": "Excellent work! The sentence accurately conveys the meaning."
        }

    def render_setup_state(self):
        """Render the setup state UI"""
        logger.debug("Entering render_setup_state")
        st.title("Japanese Writing Practice")
        
        if not self.vocabulary:
            logger.debug("No vocabulary loaded")
            st.warning("No vocabulary loaded. Please make sure a valid group_id is provided.")
            return
            
        #st.subheader(f"Group: {self.group_name}")
        
        # Add key to button to ensure proper state management
        generate_button = st.button("Generate Sentence", key="generate_sentence_btn")
        logger.debug(f"Generate button state: {generate_button}")
        
        if generate_button:
            logger.info("Generate button clicked")
            st.session_state['last_click'] = 'generate_button'
            logger.debug(f"Session state after click: {st.session_state}")
            # Pick a random word from vocabulary
            if not self.vocabulary.get('words'):
                st.error("No words found in the vocabulary group")
                return
                
            word = random.choice(self.vocabulary['words'])
            logger.debug(f"Selected word: {word.get('english')} - {word.get('kanji')}")
            
            # Generate and display the sentence
            sentence = self.generate_sentence(word)
            st.markdown("### Generated Sentence")
            st.write(sentence)
            
            # Store the current sentence and move to practice state
            st.session_state.current_sentence = sentence
            st.session_state.app_state = AppState.PRACTICE
            st.experimental_rerun()

    def render_practice_state(self):
        """Render the practice state UI"""
        st.title("Practice Japanese")
        st.write(f"English Sentence: {st.session_state.current_sentence}")
        
        uploaded_file = st.file_uploader("Upload your written Japanese", type=['png', 'jpg', 'jpeg'])
        
        if st.button("Submit for Review") and uploaded_file:
            st.session_state.review_data = self.grade_submission(uploaded_file)
            st.session_state.app_state = AppState.REVIEW
            st.experimental_rerun()

    def render_review_state(self):
        """Render the review state UI"""
        st.title("Review")
        st.write(f"English Sentence: {st.session_state.current_sentence}")
        
        review_data = st.session_state.review_data
        st.subheader("Your Submission")
        st.write(f"Transcription: {review_data['transcription']}")
        st.write(f"Translation: {review_data['translation']}")
        st.write(f"Grade: {review_data['grade']}")
        st.write(f"Feedback: {review_data['feedback']}")
        
        if st.button("Next Question"):
            st.session_state.app_state = AppState.SETUP
            st.session_state.current_sentence = ""
            st.session_state.review_data = None
            st.experimental_rerun()

    def run(self):
        """Main app loop"""
        if st.session_state.app_state == AppState.SETUP:
            self.render_setup_state()
        elif st.session_state.app_state == AppState.PRACTICE:
            self.render_practice_state()
        elif st.session_state.app_state == AppState.REVIEW:
            self.render_review_state()

# Run the app
if __name__ == "__main__":
    app = JapaneseLearningApp()
    app.run()