import boto3
import json
import re
from typing import Dict, Optional
from backend.vector_store import QuestionVectorStore

MODEL_ID = "mistral.mistral-7b-instruct-v0:2"

class QuestionGenerator:
    def __init__(self):
        """Initialize Bedrock client and vector store"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="eu-west-1")
        self.vector_store = QuestionVectorStore()
        self.model_id = MODEL_ID

    def _invoke_bedrock(self, prompt: str) -> Optional[str]:
        """Invoke Bedrock with the given prompt."""
        try:
            messages = [{
                "role": "user",
                "content": [{
                    "text": prompt
                }]
            }]
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={"temperature": 0.7}
            )
            return response['output']['message']['content'][0]['text']
        except Exception as e:
            print(f"Error invoking Bedrock: {str(e)}", flush=True)
            return None

    def _split_multiple_markers(self, line: str) -> list:
        """
        If a single line contains multiple markers (e.g. 'Einleitung:' and 'Unterhaltung:'),
        split them so each marker becomes it
        """
        markers = [
            "Einleitung:", "Introduction:",
            "Unterhaltung:", "Conversation:",
            "Situation:",
            "Frage:", "Question:",
            "Antwortmöglichkeiten:", "Options:"
        ]
        pattern = r'(' + '|'.join(re.escape(m) for m in markers) + r')'

        tokens = re.split(pattern, line)
        results = []
        current_marker = None
        current_text = []
        
        for t in tokens:
            t = t.strip()
            if not t:
                continue
            if t in markers:
                # flush old
                if current_marker or current_text:
                    results.append(f"{current_marker} {' '.join(current_text)}".strip())
                current_marker = t
                current_text = []
            else:
                current_text.append(t)
        if current_marker or current_text:
            results.append(f"{current_marker} {' '.join(current_text)}".strip())
        
        return [r for r in results if r.strip()]

    def _parse_question_response(self, response: str) -> Optional[Dict]:
        """Parse a question response into a dictionary with keys:
           Introduction, Conversation, Situation, Question, Options."""
        try:
            raw_lines = response.strip().split('\n')
            all_lines = []
            for line in raw_lines:
                splitted = self._split_multiple_markers(line)
                if splitted:
                    all_lines.extend(splitted)
                else:
                    all_lines.append(line.strip())

            question = {}
            current_key = None
            current_value = []

            for line in all_lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("Einleitung:") or line.startswith("Introduction:"):
                    if current_key:
                        if current_key == 'Options':
                            question[current_key] = current_value
                        else:
                            question[current_key] = '\n'.join(current_value)
                    current_key = 'Introduction'
                    current_value = [line.split(":", 1)[1].strip()]
                
                elif line.startswith("Unterhaltung:") or line.startswith("Conversation:"):
                    if current_key:
                        if current_key == 'Options':
                            question[current_key] = current_value
                        else:
                            question[current_key] = '\n'.join(current_value)
                    current_key = 'Conversation'
                    current_value = [line.split(":", 1)[1].strip()]
                
                elif line.startswith("Situation:"):
                    if current_key:
                        if current_key == 'Options':
                            question[current_key] = current_value
                        else:
                            question[current_key] = '\n'.join(current_value)
                    current_key = 'Situation'
                    current_value = [line.split(":", 1)[1].strip()]
                
                elif line.startswith("Frage:") or line.startswith("Question:"):
                    if current_key:
                        if current_key == 'Options':
                            question[current_key] = current_value
                        else:
                            question[current_key] = '\n'.join(current_value)
                    current_key = 'Question'
                    current_value = [line.split(":", 1)[1].strip()]

                elif line.startswith("Antwortmöglichkeiten:") or line.startswith("Options:"):
                    if current_key:
                        if current_key == 'Options':
                            question[current_key] = current_value
                        else:
                            question[current_key] = '\n'.join(current_value)
                    current_key = 'Options'
                    current_value = []
                
                elif (
                    line
                    and len(line) > 1
                    and (line[0].isdigit() or line[0].isalpha())
                    and line[1] in ['.', ')']
                    and current_key == 'Options'
                ):
                    # e.g. "1. Something"
                    current_value.append(line[2:].strip())
                else:
                    current_value.append(line)
            
            # flush last
            if current_key:
                if current_key == 'Options':
                    question[current_key] = current_value
                else:
                    question[current_key] = '\n'.join(current_value)

            return question
        except Exception as e:
            print(f"Error parsing question response: {str(e)}", flush=True)
            return None

    def generate_similar_question(self, section_num: int, topic: str) -> Optional[Dict]:
        """Attempt to generate a question based on similar existing questions."""
        similar_questions = self.vector_store.search_similar_questions(section_num, topic, n_results=3)
        print("[DEBUG] similar_questions =", similar_questions, flush=True)

        if not similar_questions:
            print("[DEBUG] No similar questions found.", flush=True)
            return None
        
        # Build context from existing questions
        context = "Hier sind einige Beispiel-Fragen zum Goethe B1 Hörverständnis:\n\n"
        for idx, q in enumerate(similar_questions, 1):
            if section_num == 2:  # Dialogue
                context += f"Beispiel {idx}:\n"
                context += f"Einleitung: {q.get('Introduction', '')}\n"
                context += f"Unterhaltung: {q.get('Conversation', '')}\n"
                context += f"Frage: {q.get('Question', '')}\n"
                if 'Options' in q:
                    context += "Antwortmöglichkeiten:\n"
                    for i, opt in enumerate(q['Options'], 1):
                        context += f"{i}. {opt}\n"
            else:  # Phrase Matching
                context += f"Beispiel {idx}:\n"
                context += f"Situation: {q.get('Situation', '')}\n"
                context += f"Frage: {q.get('Question', '')}\n"
                if 'Options' in q:
                    context += "Antwortmöglichkeiten:\n"
                    for i, opt in enumerate(q['Options'], 1):
                        context += f"{i}. {opt}\n"
            context += "\n"

        if section_num == 2:
            # Dialogue Practice prompt with random names, extra blank lines, ~200-350 words
            prompt = f"""
            Basierend auf den folgenden Beispielen zum Goethe B1 Hörverständnis,
            erstelle bitte eine neue Frage zum Thema "{topic}" in deutscher Sprache.
            Die Frage soll dem gleichen Format folgen, aber von den Beispielen abweichen.
            Achte darauf, dass die Frage das Hörverständnis testet und eine klare
            richtige Antwort hat.

            {context}

            Generiere bitte eine neue Frage im exakt gleichen Format:
            Einleitung, Unterhaltung, Frage und Antwortmöglichkeiten.

            Anforderungen:
            - Verwende zwei zufällige deutsche Vornamen (keine "None" oder leere Namen):
              Person A (männlich) und Person B (weiblich).
            - Die Unterhaltung soll ca. 200-350 Wörter lang sein.
            - Füge eine leere Zeile ein, wenn der Sprecher wechselt (z.B. Person A -> Person B).
            - Stelle sicher, dass die richtige Antwort eindeutig aus dem Gespräch hervorgeht.

            Gib NUR die Frage ohne zusätzlichen Text zurück.

            Neue Frage:
            """
        else:
            # Phrase Matching
            prompt = f"""
            Basierend auf den folgenden Beispielen zum Goethe B1 Hörverständnis,
            erstelle bitte eine neue Frage zum Thema "{topic}" in deutscher Sprache.
            Die Frage soll dem gleichen Format folgen, aber von den Beispielen abweichen.
            Achte darauf, dass die Frage das Hörverständnis testet und eine klare
            richtige Antwort hat.

            {context}

            Generiere bitte eine neue Frage im exakt gleichen Format:
            Situation, Frage und Antwortmöglichkeiten.
            Stelle sicher, dass man die richtige Antwort aus der Situation
            klar erkennen kann. Gib NUR die Frage ohne zusätzlichen Text zurück.

            Neue Frage:
            """

        response = self._invoke_bedrock(prompt)
        print("[DEBUG] Bedrock response =", response, flush=True)
        if not response:
            print("[DEBUG] Response is None; returning None.", flush=True)
            return None

        return self._parse_question_response(response)

    def generate_question(self, section_num: int, topic: str) -> Dict:
        """
        Generate a new B1 Goethe-level question. 
        1) Try to find a similar question.
        2) If none found, fallback to brand-new question in the correct format.
        """
        question = self.generate_similar_question(section_num, topic)
        if question is not None:
            return question

        # Fallback
        if section_num == 2:
            # Dialogue fallback with random names, blank lines, 200-350 words
            fallback_prompt = f"""
            Erstelle bitte eine neue B1 Goethe Hörverständnisübung in deutscher Sprache
            im exakten Format:

            Einleitung: [Kurzer Kontext, z.B. "Zwei Freunde sprechen über ein neues Fahrrad."]
            Unterhaltung: [Dialog, z.B. "Person A: ...\n\nPerson B: ...", basierend auf der Einleitung.
                           Stelle sicher, dass man die richtige Antwort aus dem Gespräch erkennt.]
            Frage: [Eine präzise Frage zum Hörverständnis, nur eine korrekte Antwort.]
            Antwortmöglichkeiten:
            1. Option eins
            2. Option zwei
            3. Option drei
            4. Option vier

            Zusätzliche Anforderungen:
            - Verwende zwei zufällige deutsche Vornamen (keine "None" oder leere Namen):
              Person A (männlich) und Person B (weiblich).
            - Die Unterhaltung soll ca. 200-350 Wörter lang sein.
            - Füge eine leere Zeile ein, wenn der Sprecher wechselt (z.B. Person A -> Person B).
            - Stelle sicher, dass die richtige Antwort eindeutig aus dem Gespräch hervorgeht.
            - Keine zusätzlichen Erklärungen oder Texte, nur das Format oben.

            Neue Frage:
            """
        else:
            fallback_prompt = f"""
            Erstelle bitte eine neue B1 Goethe Hörverständnisübung in deutscher Sprache
            im exakten Format:

            Situation: [Beschreibung der Situation, genug Details für die richtige Antwort]
            Frage: [Eine präzise Frage zum Hörverständnis]
            Antwortmöglichkeiten:
            1. Option eins
            2. Option zwei
            3. Option drei
            4. Option vier

            Bitte stelle sicher, dass die Situation genug Details enthält,
            um die richtige Antwort klar zu machen. Keine zusätzlichen Erklärungen
            oder Texte, nur das Format oben.

            Neue Frage:
            """

        response = self._invoke_bedrock(fallback_prompt)
        print("[DEBUG] Fallback response =", response, flush=True)
        if not response:
            return {}

        question = self._parse_question_response(response)
        print("[DEBUG] Final parsed fallback question =", question, flush=True)
        return question if question else {}

    def get_feedback(self, question: Dict, selected_answer: int) -> Dict:
        """Generate feedback for the selected answer."""
        if not question or 'Options' not in question:
            return None

        prompt = f"""
            Gegeben diese Goethe B1 Hörverständnisfrage und die ausgewählte
            Antwort, gib bitte ein Feedback, das erklärt, ob die Antwort korrekt
            ist und warum. Halte die Erklärung klar und präzise.
        """
        if 'Introduction' in question:
            prompt += f"Einleitung: {question['Introduction']}\n"
            prompt += f"Unterhaltung: {question.get('Conversation', '')}\n"
        elif 'Situation' in question:
            prompt += f"Situation: {question['Situation']}\n"

        prompt += f"Frage: {question.get('Question','')}\n"
        prompt += "Antwortmöglichkeiten:\n"
        for i, opt in enumerate(question['Options'], 1):
            prompt += f"{i}. {opt}\n"

        prompt += f"\nAusgewählte Antwort: {selected_answer}\n"
        prompt += "\nGib bitte Feedback im JSON-Format mit den folgenden Feldern an:\n"
        prompt += "- correct: true/false\n"
        prompt += "- explanation: kurze Erklärung, warum die Antwort korrekt oder nicht korrekt ist\n"
        prompt += "- correct_answer: die Nummer der korrekten Antwort (1-4)\n"

        response = self._invoke_bedrock(prompt)
        if not response:
            return None

        try:
            feedback = json.loads(response.strip())
            return feedback
        except Exception:
            return {
                "correct": False,
                "explanation": "Unable to generate detailed feedback. Please try again.",
                "correct_answer": 1
            }
