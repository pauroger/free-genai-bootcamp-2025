import json
from gtts import gTTS
import os

# Load the JSON dataset
with open("../lang-portal/backend-flask/seed/data_adjectives.json", "r", encoding="utf-8") as f:
    words = json.load(f)

# Create output directories for English and German words
os.makedirs("audio/en", exist_ok=True)
os.makedirs("audio/de", exist_ok=True)

for word in words:
    german_word = word["german"]
    english_word = word["english"].replace(" ", "_").replace(";", "")

    # Generate German audio and save it in the 'de' folder
    tts_german = gTTS(text=german_word, lang="de")
    tts_german.save(f"audio/de/{german_word}.mp3")

    # Generate English audio and save it in the 'en' folder
    tts_english = gTTS(text=word["english"], lang="en")
    tts_english.save(f"audio/en/{english_word}.mp3")

print("MP3 files generated successfully in 'audio/en' and 'audio/de'!")
