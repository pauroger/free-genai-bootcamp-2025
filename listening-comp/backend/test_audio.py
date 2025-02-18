import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.audio_generator import AudioGenerator

# German test question data
test_question = {
    "Introduction": "Hören Sie sich das folgende Gespräch an und beantworten Sie die Frage.",
    "Conversation": """
        male: Entschuldigen Sie, hält dieser Zug am Hauptbahnhof?
        female: Ja, der nächste Halt ist der Hauptbahnhof.
        male: Vielen Dank. Wie lange dauert die Fahrt?
        female: Ungefähr 5 Minuten.
    """,
    "Question": "Wie lange dauert die Fahrt zum Hauptbahnhof?",
    "Options": [
        "3 Minuten",
        "5 Minuten",
        "10 Minuten",
        "15 Minuten"
    ]
}

def test_audio_generation():
    print("Initializing audio generator...")
    generator = AudioGenerator()
    
    print("\nParsing conversation...")
    parts = generator.parse_conversation(test_question)
    
    print("\nParsed conversation parts:")
    for speaker, text, gender in parts:
        print(f"Speaker: {speaker} ({gender})")
        print(f"Text: {text}")
        print("---")
    
    print("\nGenerating audio file...")
    # Pass the German language code so that German voices are used
    audio_file = generator.generate_audio(test_question, language_code="de-DE")
    print(f"Audio file generated: {audio_file}")
    
    return audio_file

if __name__ == "__main__":
    try:
        audio_file = test_audio_generation()
        print("\nTest completed successfully!")
        print(f"You can find the audio file at: {audio_file}")
    except Exception as e:
        print(f"\nError during test: {str(e)}")
