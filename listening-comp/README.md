# Listening Comprehension

A Streamlit-based application for listening comprehension and dialogue practice in German, featuring AI-generated scenarios and audio.

Sample Question:

![App Sample Screenshot](frontend/images/Listening%20App%201.png)

Sample Answer:

![App Sample Screenshot](frontend/images/Listening%20App%202.png)

## How It Works

- Users select a practice type (currently "Dialogue Practice") and a topic
- The system generates a scenario with a question and multiple-choice answers
- Audio is automatically generated for the dialogue
- Users listen to the audio and select their answer
- The system provides immediate feedback and explanations
- Questions are saved for future practice sessions

## Run the frontend

```sh
streamlit run frontend/main.py --server.port=8502
```
