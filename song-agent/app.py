import sys
import os
from pathlib import Path
import json
import re
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))

from agent import run_language_tutor
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

# Set page config as the VERY FIRST Streamlit command
st.set_page_config(
    page_title="Song Language Tutor",
    page_icon="🎵",
    layout="wide",
)

apply_custom_theme(primary_color="#90cdec")

# Only add custom styling for specific components not covered by the theme
st.markdown("""
<style>
    .lyrics-container {
        height: 5px;
        overflow-y: auto;
        padding: 15px;
        background-color: white;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    
    .vocab-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-left: 4px solid #90cdec;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def check_if_song_exists(song_title):
    """Check if the song analysis file already exists"""
    filename = f'songs/{song_title}_song_analysis.json'
    return os.path.exists(filename)

def load_song_analysis(song_title):
    """Load the song analysis from the JSON file"""
    filename = f'songs/{song_title}_song_analysis.json'
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        error_box(f"File not found: {filename}")
        return None
    except json.JSONDecodeError:
        error_box(f"Invalid JSON in file: {filename}")
        return None

def display_song_analysis(analysis_data):
    """Display the song analysis in a pretty way"""
    if not analysis_data:
        return
    
    # Display song title and language info
    st.title(f"🎵 Analysis of '{st.session_state.song_title}'")
    highlight(f"🔍 From {st.session_state.foreign_language} to {st.session_state.user_language}")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Lyrics & Intent", "📚 Vocabulary", "🔍 Search Results", "📄 Source Content"])
    
    with tab1:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("📝 Lyrics")
            st.markdown("<div class='lyrics-container'>", unsafe_allow_html=True)
            for line in analysis_data["extract_vocabulary"]["lyrics"]:
                st.markdown(f"_{line}_")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.subheader("🧠 Meaning & Context")
            highlight(analysis_data['intent'])
    
    with tab2:
        st.subheader("📚 Key Vocabulary")
        
        # Display vocabulary as a grid of cards
        vocab_list = analysis_data["extract_vocabulary"]["vocabulary_list"]
        cols = st.columns(2)
        
        for i, word_data in enumerate(vocab_list):
            col_idx = i % 2
            with cols[col_idx]:
                st.markdown(f"""
                <div class='vocab-card'>
                    <h3>🔤 {word_data['word']}</h3>
                    <p><strong>Meaning:</strong> {word_data['meaning']}</p>
                    <p><strong>Example:</strong> <em>{word_data['example']}</em></p>
                </div>
                """, unsafe_allow_html=True)
        
        # Display all words in a collapsible section
        with st.expander("See all extracted words"):
            # Convert words list to a DataFrame for better display
            all_words = analysis_data["extract_vocabulary"]["words"]
            # Split into columns for better display
            cols_per_row = 4
            rows = [all_words[i:i+cols_per_row] for i in range(0, len(all_words), cols_per_row)]
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
    
    with tab3:
        st.subheader("🔍 Search Results")
        for i, result in enumerate(analysis_data["search_results"]):
            st.markdown(f"{i+1}. [{result['title']}]({result['url']})")
    
    with tab4:
        st.subheader("📄 Source Content")
        if isinstance(analysis_data["get_page_content"], dict) and "url" in analysis_data["get_page_content"]:
            st.markdown(f"Source: [{analysis_data['get_page_content']['url']}]({analysis_data['get_page_content']['url']})")
            
            with st.expander("View Raw Content"):
                content = analysis_data["get_page_content"]["content"]
                st.text_area("Raw Content", content, height=400)
        else:
            st.write("Source information not available in the expected format.")

# Create a songs directory if it doesn't exist
if not os.path.exists('songs'):
    os.makedirs('songs')

# Main app layout
st.title("🎵 Song Language Tutor")
info_box("Learn a new language by exploring songs! Enter a song title below, and we'll fetch lyrics and provide vocabulary explanations to help you understand and learn.")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Initialize session state for settings if not already done
    if 'user_language' not in st.session_state:
        st.session_state.user_language = "English"
    if 'foreign_language' not in st.session_state:
        st.session_state.foreign_language = "German"
    if 'song_title' not in st.session_state:
        st.session_state.song_title = ""
    
    # Settings inputs
    st.session_state.user_language = st.selectbox(
        "Your Language", 
        ["English", "Catalan", "French", "German", "Italian", "Portuguese"],
        index=["English", "Catalan", "French", "German", "Italian", "Portuguese"].index(st.session_state.user_language)
    )
    
    st.session_state.foreign_language = st.selectbox(
        "Song Language", 
        ["German", "Catalan", "French", "English", "Italian", "Portuguese"],
        index=["German", "Catalan", "French", "English", "Italian", "Portuguese"].index(st.session_state.foreign_language)
    )
    
    # List available analyzed songs
    st.markdown("### 📂 Analyzed Songs")
    songs_pattern = re.compile(r'(.+)_song_analysis\.json')
    if os.path.exists('songs'):
        analyzed_songs = []
        for filename in os.listdir('songs'):
            match = songs_pattern.match(filename)
            if match:
                analyzed_songs.append(match.group(1))
        
        if analyzed_songs:
            st.write("Click to load an already analyzed song:")
            for song in analyzed_songs:
                if st.button(f"🎵 {song}", key=f"btn_{song}"):
                    st.session_state.song_title = song
                    st.rerun()
        else:
            st.write("No analyzed songs yet.")

# Song input and analysis
st.subheader("🔍 Enter a Song to Analyze")
song_title_input = st.text_input("Song Title", placeholder="e.g. Die Philosoffen")

if st.button("Analyze Song", type="primary") and song_title_input:
    st.session_state.song_title = song_title_input
    
    with st.spinner("Loading song analysis..."):
        if check_if_song_exists(song_title_input):
            success_box(f"Found existing analysis for '{song_title_input}'!")
            analysis_data = load_song_analysis(song_title_input)
        else:
            info_box(f"Analyzing new song: '{song_title_input}'...")
            # Import the agent function
            try:
                # This function should return the analysis results
                analysis_data = run_language_tutor(
                    song_title=song_title_input,
                    user_language=st.session_state.user_language,
                    foreign_language=st.session_state.foreign_language
                )
                success_box("Analysis complete!")
            except Exception as e:
                error_box(f"Error analyzing song: {str(e)}")
                analysis_data = None
        
        if analysis_data:
            display_song_analysis(analysis_data)

# Display previously loaded song if in session state
elif st.session_state.song_title:
    analysis_data = load_song_analysis(st.session_state.song_title)
    if analysis_data:
        display_song_analysis(analysis_data)
    else:
        warning_box("Couldn't load analysis data. Please try analyzing the song again.")
