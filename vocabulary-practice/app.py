import sys
from pathlib import Path
import requests
import random

sys.path.append(str(Path(__file__).parent.parent))

from themes.gradio_theme import apply_custom_theme

theme = apply_custom_theme(primary_color="#90cdec")

import gradio as gr

BACKEND_URL = "http://127.0.0.1:5000"
SCRIPT_DIR = Path(__file__).parent

def log_message(message):
    with open("log.txt", "a") as logfile:
        logfile.write(message + "\n")

def fetch_random_word(current_group):
    try:
        log_message(f"Fetching random word for group: {current_group}")
        response = requests.get(f"{BACKEND_URL}/groups/{current_group}/words/raw")
        log_message(f"HTTP GET request to: {BACKEND_URL}/groups/{current_group}/words/raw, status code: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        words = data.get("raw_words", [])
        if not words:
            log_message("No words found for this group.")
            return None, "🟡 No words found for this group.", None
        random_word = random.choice(words)
        log_message("\nSelected random word: " + str(random_word))
        english = random_word.get("english", "Unknown")
        log_message("\nSelected random word english: " + str(english))
        german = random_word.get("german", "Unknown")
        word_id = random_word.get("id", None)
        log_message(f"Returning word - English: {english}, German: {german}, ID: {word_id}")
        return english, german, word_id
    except requests.exceptions.RequestException as e:
        log_message(f"❌ Error fetching data: {e}")
        return None, f"❌ Error fetching data: {e}", None


def generate_word(current_group):
    english_word, correct_german, word_id = fetch_random_word(current_group)
    if not english_word:
        return "", "", correct_german, None
    return english_word, "", correct_german, word_id

def get_url_params():
    import urllib.parse
    import os
    
    url_path = os.environ.get('GRADIO_SERVER_PATH', '')
    if '?' in url_path:
        query = url_path.split('?')[1]
        return dict(urllib.parse.parse_qsl(query))
    return {}

def init_game(request: gr.Request):
    url_params = get_url_params()
    log_message(f"URL params: {url_params}")
    
    group_id = url_params.get("group_id", "1") 
    session_id = url_params.get("session_id")
    
    log_message(f"Using group_id: {group_id}, session_id: {session_id}")
    
    if not group_id:
        return session_id, None, "No group id provided.", "", "", None

    english_word, correct_german, word_id = fetch_random_word(group_id)
    return session_id, group_id, english_word, "", correct_german, word_id

def check_answer(user_input, english_word, correct_german, review_items, current_word_id):
    correct = user_input.strip().lower() == correct_german.lower()
    log_message(f"\n\current_id: {current_word_id}")
    log_message(f"\n\correct: {correct}")
    if correct:
        message = f"<p style='color:green;'>✅ Correct! '{english_word}' in German is '{correct_german}'.</p>"
    else:
        message = f"<p style='color:red;'>❌ Incorrect. '{english_word}' in German is '{correct_german}'.</p>"
    review_items = review_items or []
    review_items.append({"word_id": current_word_id, "correct": correct})
    log_message(f"\n\review_items: {review_items}")
    if correct:
        return gr.update(value=message, visible=True), gr.update(value="", visible=False), review_items
    else:
        return gr.update(value="", visible=False), gr.update(value=message, visible=True), review_items

def save_study_session(study_session_id, review_items, current_group):
    log_message(f"\n\study_session_id: {study_session_id}")
    log_message(f"\nreview_items: {review_items}")
    log_message(f"\n\current_group: {current_group}")
    if not review_items:
        return study_session_id, []
    if not study_session_id:
        payload = {"group_id": current_group, "study_activity_id": 2}
        try:
            response = requests.post(f"{BACKEND_URL}/study_sessions", json=payload)
            log_message(f"\n\response: {response}")
            response.raise_for_status()
            data = response.json()
            study_session_id = data["session_id"]
        except Exception as e:
            raise gr.Error(f"Failed to create study session: {e}")
    for item in review_items:
        payload = {"word_id": item["word_id"], "correct": item["correct"]}
        log_message(f"\n\npayload: {payload}")
        try:
            response = requests.post(f"{BACKEND_URL}/study_sessions/{study_session_id}/review", json=payload)
            response.raise_for_status()
            log_message(f"\n\response: {response}")
        except Exception as e:
            raise gr.Error("Failed to save study session")
    gr.Info("💾 Study session saved!")
    return study_session_id, []

with gr.Blocks(
    theme=theme,
    css="""
.center {
    display: flex;
    justify-content: center;
    width: 50%;
}
""") as demo:
    gr.HTML("<h1> ✍🏼 English to German Vocabulary Practice </h1>")

    study_session_state = gr.State(None)
    review_items_state = gr.State([])
    current_group_state = gr.State(None)
    
    with gr.Row():
        english_output = gr.Textbox(label="English Word", interactive=False)
        answer_input = gr.Textbox(label="Your Answer in german")
    
    hidden_correct = gr.Textbox(visible=False)
    hidden_id = gr.Textbox(visible=False)
    
    result_success = gr.Markdown(visible=False)
    result_error = gr.Markdown(visible=False)
    
    with gr.Row():
        check_button = gr.Button("Check Answer", variant="primary")
        save_button = gr.Button("Save Study Session", variant="primary")
    
    demo.load(fn=init_game, outputs=[study_session_state, current_group_state, english_output, answer_input, hidden_correct, hidden_id])
    
    check_button.click(fn=check_answer,
                       inputs=[answer_input, english_output, hidden_correct, review_items_state, hidden_id],
                       outputs=[result_success, result_error, review_items_state])
    check_button.click(fn=generate_word,
                       inputs=current_group_state,
                       outputs=[english_output, answer_input, hidden_correct, hidden_id])
    
    save_button.click(fn=save_study_session,
                      inputs=[study_session_state, review_items_state, current_group_state],
                      outputs=[study_session_state, review_items_state])
    save_button.click(lambda: gr.update(value="", visible=False), outputs=result_error)

    save_notification = gr.Markdown(visible=False)

    save_button.click(
        fn=save_study_session,
        inputs=[study_session_state, review_items_state, current_group_state],
        outputs=[study_session_state, review_items_state]
    )
    save_button.click(
        fn=lambda: gr.update(value="**💾 Study session saved successfully!**", visible=True),
        outputs=save_notification
    )

    check_button.click(
        fn=lambda: gr.update(visible=False),
        outputs=save_notification
    )
    
    gr.Markdown("Save progress and close the tab when finished.")

demo.launch(server_port=6001, server_name="127.0.0.1", show_error=True)