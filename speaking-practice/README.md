# 🗣️ German Speaking Tutor

A Gradio application that helps users practice German speaking skills through
image description exercises.

Sample Song:

![App Sample Screenshot](/lang-portal/frontend-react/public/SpeakingTutor.png)

## Features

- **Image Generation**: Creates random scenes in three categories (Landscape, City, Interaction)
- **Speech Practice**: Record yourself describing images in German (up to 2 minutes)  
- **Transcription**: Converts your German speech to text using OpenAI Whisper
- **Evaluation**: Provides CEFR-level feedback on fluency, vocabulary, grammar, and description accuracy

## Run the application

```bash
gradio app.py
```

## Technical Details

- Uses AWS Bedrock `amazon.titan-image-generator-v1` to generate the image to describe
- Uses OpenAI's Whisper model for German speech transcription
- Uses OpenAI's GPT model for language evaluation
- Evaluates against CEFR language proficiency standards (A1-C2)
- Custom image generation based on random configurations
