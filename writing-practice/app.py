import boto3
import json
import sys
from pathlib import Path

# Initialize the Bedrock runtime client in the eu-west-1 region
client = boto3.client('bedrock-runtime', region_name='eu-west-1')
MODEL_ID = "mistral.mistral-large-2402-v1:0"
# MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

sys.path.append(str(Path(__file__).parent.parent))

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

st.set_page_config(
    page_title="Writting Tutor",
    page_icon="✍️",
)

apply_custom_theme(primary_color="#90cdec")

def parse_response(response):
    raw_body = response.get("body")
    if hasattr(raw_body, "read"):
        raw_body = raw_body.read()
        if isinstance(raw_body, bytes):
            raw_body = raw_body.decode("utf-8")
    # Debug: Print the raw response
    # st.write("Raw response:", raw_body)
    return json.loads(raw_body)

def generate_target_sentence():
    messages = [
        {"role": "user", "content": "Generate an English sentence that is scoped to Goethe B1 grammar. Provide just the sentence."}
    ]
    response = client.invoke_model(
        modelId=MODEL_ID,
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            "messages": messages,
            "max_tokens": 5000,
        })
    )
    result = parse_response(response)
    if "choices" in result and result["choices"]:
        return result["choices"][0]["message"]["content"].strip()
    return "No sentence generated."


def grade_submission(target_sentence, submission):
    messages = [
        {"role": "user", "content": (
            f"Grade this German writing sample:\n\n"
            f"Target English sentence:\n{target_sentence}\n\n"
            f"Student's German translation:\n{submission}\n\n"
            "Grading Criteria:\n"
            "- Accuracy of translation compared to the target sentence\n"
            "- Grammar correctness\n"
            "- Writing style and naturalness\n\n"
            "Grading scale:\n"
            "S: Perfect or near-perfect\n"
            "A: Very good with minor issues\n"
            "B: Good but needs improvement\n"
            "C: Significant issues to address\n\n"
            "Please provide your grade (S/A/B/C) and detailed feedback including whether the attempt was accurate to the English sentence and suggestions for improvement."
            "*Correct Sentence:*"
        )}
    ]
    response = client.invoke_model(
        modelId=MODEL_ID,
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            "messages": messages,
            "max_tokens": 256,
        })
    )
    result = parse_response(response)
    if "choices" in result and result["choices"]:
        return result["choices"][0]["message"]["content"].strip()
    return "No assessment provided."

# Initialize session state if not present
if "target_sentence" not in st.session_state:
    st.session_state.target_sentence = generate_target_sentence()
if "graded_output" not in st.session_state:
    st.session_state.graded_output = ""
if "submission" not in st.session_state:
    st.session_state.submission = ""

st.title("English to German Writing Practice")

st.header("Translate the following sentence into German:")
st.write(st.session_state.target_sentence)

st.session_state.submission = st.text_area("Your German translation", st.session_state.submission)

if st.button("Submit"):
    st.session_state.graded_output = grade_submission(st.session_state.target_sentence, st.session_state.submission)
    st.write("### Grading")
    st.write(st.session_state.graded_output)

if st.button("Next Question"):
    # Reset the session state and generate a new sentence
    st.session_state.target_sentence = generate_target_sentence()
    st.session_state.submission = ""
    st.session_state.graded_output = ""
