import streamlit as st
import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.question_generator import QuestionGenerator
from backend.audio_generator import AudioGenerator

# Page config
st.set_page_config(
    page_title="German Practice",
    page_icon="🎧",
    layout="wide"
)

def load_stored_questions():
    """Load previously stored questions from JSON file"""
    questions_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend", "data", "stored_questions.json"
    )
    if os.path.exists(questions_file):
        with open(questions_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_question(question, practice_type, topic, audio_file=None):
    """Save a generated question to JSON file"""
    questions_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend", "data", "stored_questions.json"
    )
    
    stored_questions = load_stored_questions()
    question_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    question_data = {
        "question": question,
        "practice_type": practice_type,
        "topic": topic,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "audio_file": audio_file
    }
    
    stored_questions[question_id] = question_data
    os.makedirs(os.path.dirname(questions_file), exist_ok=True)
    with open(questions_file, 'w', encoding='utf-8') as f:
        json.dump(stored_questions, f, ensure_ascii=False, indent=2)
    
    return question_id

def clean_text(text: str) -> str:
    """Remove unwanted 'None' strings and extra whitespace."""
    if not text:
        return ""
    return text.replace("None", "").strip()

def format_conversation(conv_text: str) -> str:
    """
    Insert an extra blank line every time the speaker changes.
    We assume that speaker lines start with "Person A:" or "Person B:".
    """
    if not conv_text:
        return ""
    conv_text = clean_text(conv_text)
    lines = conv_text.split('\n')
    formatted_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Person A:") or stripped.startswith("Person B:"):
            if formatted_lines and formatted_lines[-1].strip() != "":
                formatted_lines.append("")  # add an extra blank line
        formatted_lines.append(stripped)
    return "\n".join(formatted_lines)

def render_interactive_stage():
    # Initialize session state
    if 'question_generator' not in st.session_state:
        st.session_state.question_generator = QuestionGenerator()
    if 'audio_generator' not in st.session_state:
        st.session_state.audio_generator = AudioGenerator()
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'feedback' not in st.session_state:
        st.session_state.feedback = None
    if 'current_practice_type' not in st.session_state:
        st.session_state.current_practice_type = None
    if 'current_topic' not in st.session_state:
        st.session_state.current_topic = None
    if 'current_audio' not in st.session_state:
        st.session_state.current_audio = None
    if 'selected_answer' not in st.session_state:
        st.session_state.selected_answer = None

    # Sidebar: load stored questions
    stored_questions = load_stored_questions()
    with st.sidebar:
        st.header("Saved Questions")
        if stored_questions:
            for qid, qdata in stored_questions.items():
                button_label = f"{qdata['practice_type']} - {qdata['topic']}\n{qdata['created_at']}"
                if st.button(button_label, key=qid):
                    st.session_state.current_question = qdata['question']
                    st.session_state.current_practice_type = qdata['practice_type']
                    st.session_state.current_topic = qdata['topic']
                    st.session_state.current_audio = qdata.get('audio_file')
                    st.session_state.feedback = None
                    st.session_state.selected_answer = None
        else:
            st.info("No saved questions yet. Generate some questions to see them here!")
    
    # Practice type and topic selection
    practice_type = st.selectbox(
        "Select Practice Type",
        ["Dialogue Practice", "Phrase Matching"]
    )
    topics = {
        "Dialogue Practice": ["Daily Conversation", "Shopping", "Restaurant", "Travel", "School/Work"],
        "Phrase Matching": ["Announcements", "Instructions", "Weather Reports", "News Updates"]
    }
    topic = st.selectbox("Select Topic", topics[practice_type])
    
    # Generate new question button
    if st.button("Generate New Question"):
        section_num = 2 if practice_type == "Dialogue Practice" else 3
        new_question = st.session_state.question_generator.generate_question(section_num, topic)
        st.session_state.current_question = new_question
        st.session_state.current_practice_type = practice_type
        st.session_state.current_topic = topic
        st.session_state.feedback = None
        st.session_state.selected_answer = None
        save_question(new_question, practice_type, topic)
        st.session_state.current_audio = None

    if st.session_state.current_question:
        st.subheader("Practice Scenario")
        
        if practice_type == "Dialogue Practice":
            introduction = clean_text(st.session_state.current_question.get('Introduction', ''))
            st.write("**Introduction:**")
            st.write(introduction if introduction else "—")
            
            # Hide conversation until answer is submitted
            if st.session_state.feedback:
                conversation = clean_text(st.session_state.current_question.get('Conversation', ''))
                prettified_conv = format_conversation(conversation)
                st.write("**Conversation:**")
                st.markdown(prettified_conv)
            else:
                st.info("The conversation will be revealed after you submit your answer.")
        else:
            situation = clean_text(st.session_state.current_question.get('Situation', ''))
            st.write("**Situation:**")
            st.write(situation if situation else "—")
        
        # Automatically generate audio if not already generated
        if st.session_state.current_audio is None:
            with st.spinner("Generating audio..."):
                try:
                    if st.session_state.current_audio and os.path.exists(st.session_state.current_audio):
                        try:
                            os.unlink(st.session_state.current_audio)
                        except Exception:
                            pass
                    st.session_state.current_audio = None
                    audio_file = st.session_state.audio_generator.generate_audio(
                        st.session_state.current_question
                    )
                    if not os.path.exists(audio_file):
                        raise Exception("Audio file was not created")
                    st.session_state.current_audio = audio_file
                    save_question(
                        st.session_state.current_question,
                        st.session_state.current_practice_type,
                        st.session_state.current_topic,
                        audio_file
                    )
                except Exception as e:
                    st.error(f"Error generating audio: {str(e)}")
                    st.session_state.current_audio = None
        
        # Display audio widget under Practice Scenario
        st.audio(st.session_state.current_audio)
        
        st.write("**Question:**")
        question_text = clean_text(st.session_state.current_question.get('Question', ''))
        st.write(question_text if question_text else "—")
        
        # Display answer options and handle response
        raw_options = st.session_state.current_question.get('Options', [])
        options = [clean_text(opt) for opt in raw_options if clean_text(opt) != ""]
        
        if st.session_state.feedback:
            correct = st.session_state.feedback.get('correct', False)
            correct_answer = st.session_state.feedback.get('correct_answer', 1) - 1
            selected_index = st.session_state.selected_answer - 1 if st.session_state.selected_answer else -1
            
            st.write("\n**Your Answer:**")
            for i, option in enumerate(options):
                if i == correct_answer and i == selected_index:
                    st.success(f"{i+1}. {option} ✓ (Correct!)")
                elif i == correct_answer and i != selected_index:
                    st.info(f"{i+1}. {option} ✓ (Correct Answer)")
                elif i == selected_index and i != correct_answer:
                    st.error(f"{i+1}. {option} ✗ (Your answer)")
                else:
                    st.write(f"{i+1}. {option}")
            
            st.write("\n**Explanation:**")
            explanation = clean_text(st.session_state.feedback.get('explanation', 'No feedback available'))
            if correct:
                st.success(explanation)
            else:
                st.error(explanation)
            
            if st.button("Try Another Question"):
                st.session_state.feedback = None
                st.session_state.selected_answer = None
                st.session_state.current_question = None
                st.session_state.current_audio = None
        else:
            selected = st.radio(
                "Choose your answer:",
                options,
                index=None,
                format_func=lambda x: f"{options.index(x) + 1}. {x}"
            )
            if selected and st.button("Submit Answer"):
                selected_index = options.index(selected) + 1
                st.session_state.selected_answer = selected_index
                st.session_state.feedback = st.session_state.question_generator.get_feedback(
                    st.session_state.current_question,
                    selected_index
                )
    else:
        st.info("Click 'Generate New Question' to start practicing!")

def main():
    st.title("German Practice")
    render_interactive_stage()

if __name__ == "__main__":
    main()
