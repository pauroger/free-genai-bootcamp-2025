import json
import os
from gtts import gTTS

# Paths
INPUT_JSON = "../lang-portal/backend-flask/seed/data_verbs.json"
OUTPUT_JSON = "./datasets/words.json"
AUDIO_DIR = "audio"

# Load the JSON dataset
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    words = json.load(f)

# Ensure output directories exist
os.makedirs(os.path.join(AUDIO_DIR, "en"), exist_ok=True)
os.makedirs(os.path.join(AUDIO_DIR, "de"), exist_ok=True)

# Prepare a list to store processed words for words.json
processed_words = []

for word in words:
    german_word = word["german"]
    english_word = word["english"].replace(" ", "_").replace(";", "")

    # File paths
    german_audio_path = os.path.join(AUDIO_DIR, "de", f"{german_word}.mp3")
    english_audio_path = os.path.join(AUDIO_DIR, "en", f"{english_word}.mp3")

    # Generate German audio
    tts_german = gTTS(text=german_word, lang="de")
    tts_german.save(german_audio_path)

    # Generate English audio
    tts_english = gTTS(text=word["english"], lang="en")
    tts_english.save(english_audio_path)

    # Append processed words to list
    processed_words.append({
        "german": german_word,
        "english": word["english"],
        "parts": word.get("parts", [])  # Include "parts" if available
    })

# Save processed words to words.json
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(processed_words, f, indent=4, ensure_ascii=False)

print("MP3 files generated successfully in 'audio/en' and 'audio/de'!")
print(f"Processed words saved to {OUTPUT_JSON}")
