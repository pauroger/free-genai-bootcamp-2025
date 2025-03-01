import gradio as gr
import requests
import random
from gradio.themes import GoogleFont

# Create a custom theme:
# - Use Nunito as the font.
# - Set primary button background to #55CD02 in both light and dark modes.
# - In dark mode, set the body background to #333333.
theme = gr.themes.Default(font=[GoogleFont("Nunito")]).set(
    button_primary_background_fill="#55CD02",
    button_primary_background_fill_dark="#55CD02",
    body_background_fill_dark="#333333"
)

# Backend URL
BACKEND_URL = "http://127.0.0.1:5000"

# def fetch_random_word(current_group):
#     try:
#         response = requests.get(f"{BACKEND_URL}/groups/{current_group}/words/raw")
#         response.raise_for_status()
#         data = response.json()
#         words = data.get("raw_words", [])
#         if not words:
#             return None, "🟡 No words found for this group.", None
#         random_word = random.choice(words)
#         english = random_word.get("english", "Unknown")
#         german = random_word.get("german", "Unknown")
#         word_id = random_word.get("word_id", None)
#         return english, german, word_id
#     except requests.exceptions.RequestException as e:
#         return None, f"❌ Error fetching data: {e}", None

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
        return english, german, id
    except requests.exceptions.RequestException as e:
        log_message(f"❌ Error fetching data: {e}")
        return None, f"❌ Error fetching data: {e}", None


def generate_word(current_group):
    english_word, correct_german, word_id = fetch_random_word(current_group)
    if not english_word:
        return "", "", correct_german, None
    return english_word, "", correct_german, id

def init_game(request: gr.Request):
    params = dict(request.query_params)
    group_id = params.get("group_id")
    session_id = params.get("session_id")
    
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
            study_session_id = data["word_id"]
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
    gr.Info("💾 Study session saved!", duration=2)
    return study_session_id, []

# Create Blocks with custom CSS to center content.
with gr.Blocks(
    theme=theme,
    css="""
.center {
    display: flex;
    justify-content: center;
    width: 50%;
}
""") as demo:
    gr.HTML("<h1> ✍🏼 English to german Writing Practice </h1>")
    
    # States for study session, review items, and current group.
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
    
    gr.Markdown("Save progress and close the tab when finished.")
    with gr.Row(elem_classes="center"):
        gr.Image(
            value="Writing Practice.png", 
            show_label=False,
            show_download_button=False,
            show_fullscreen_button=False,
            container=False
        )

demo.launch()
