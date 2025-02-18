import boto3
import json
from typing import Dict, Optional
from vector_store import QuestionVectorStore

MODEL_ID = "mistral.mistral-7b-instruct-v0:2" 


class QuestionGenerator:
    def __init__(self):
        """Initialize Bedrock client and vector store"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="eu-west-1")
        self.vector_store = QuestionVectorStore()
        self.model_id = MODEL_ID

    def _invoke_bedrock(self, prompt: str) -> Optional[str]:
        """Invoke Bedrock with the given prompt"""
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
            print(f"Error invoking Bedrock: {str(e)}")
            return None

    def generate_similar_question(self, section_num: int, topic: str) -> Dict:
        """Generate a new question similar to existing ones on a given topic
        (German B1 level by Goethe)"""
        # Get similar questions for context
        similar_questions = self.vector_store.search_similar_questions(section_num, topic, n_results=3)
        
        if not similar_questions:
            return None
        
        # Create context from similar questions in German
        context = "Hier sind einige Beispiel-Fragen zum Goethe B1 Hörverständnis:\n\n"
        for idx, q in enumerate(similar_questions, 1):
            if section_num == 2:
                context += f"Beispiel {idx}:\n"
                context += f"Einleitung: {q.get('Introduction', '')}\n"
                context += f"Unterhaltung: {q.get('Conversation', '')}\n"
                context += f"Frage: {q.get('Question', '')}\n"
                if 'Options' in q:
                    context += "Antwortmöglichkeiten:\n"
                    for i, opt in enumerate(q['Options'], 1):
                        context += f"{i}. {opt}\n"
            else:  # section 3
                context += f"Beispiel {idx}:\n"
                context += f"Situation: {q.get('Situation', '')}\n"
                context += f"Frage: {q.get('Question', '')}\n"
                if 'Options' in q:
                    context += "Antwortmöglichkeiten:\n"
                    for i, opt in enumerate(q['Options'], 1):
                        context += f"{i}. {opt}\n"
            context += "\n"

        # Create prompt in German for generating a new question
        prompt = f"""
        Basierend auf den folgenden Beispielen zum Goethe B1 Hörverständnis,
        erstelle bitte eine neue Frage zum Thema "{topic}" in deutscher Sprache.
        Die Frage soll dem gleichen Format folgen, aber von den Beispielen
        abweichen. Achte darauf, dass die Frage das Hörverständnis testet und
        eine klare richtige Antwort hat.

        {context}

        Generiere bitte eine neue Frage im exakt gleichen Format. Füge alle
        Komponenten ein (Einleitung/Situation, Unterhaltung/Frage und
        Antwortmöglichkeiten). Die Frage soll herausfordernd, aber fair sein,
        und die Antwortmöglichkeiten müssen plausibel sein, wobei nur eine
        eindeutig korrekte Antwort existiert. Gib NUR die Frage ohne
        zusätzlichen Text zurück.

        Neue Frage:
        """

        # Generate new question
        response = self._invoke_bedrock(prompt)
        if not response:
            return None

        # Parse the generated question
        try:
            lines = response.strip().split('\n')
            question = {}
            current_key = None
            current_value = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Handle Introduction/Einleitung
                if line.startswith("Einleitung:") or line.startswith("Introduction:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Introduction'
                    current_value = [line.split(":", 1)[1].strip()]
                # Handle Conversation/Unterhaltung
                elif line.startswith("Unterhaltung:") or line.startswith("Conversation:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Conversation'
                    current_value = [line.split(":", 1)[1].strip()]
                # Handle Situation (remains the same)
                elif line.startswith("Situation:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Situation'
                    current_value = [line.split(":", 1)[1].strip()]
                # Handle Question/Frage
                elif line.startswith("Frage:") or line.startswith("Question:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Question'
                    current_value = [line.split(":", 1)[1].strip()]
                # Handle Options/Antwortmöglichkeiten
                elif line.startswith("Antwortmöglichkeiten:") or line.startswith("Options:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Options'
                    current_value = []
                # Handle option lines (accept letters or numbers)
                elif (line[0].isdigit() or line[0].isalpha()) and (line[1] in ['.', ')']) and current_key == 'Options':
                    current_value.append(line[2:].strip())
                elif current_key:
                    current_value.append(line)

            if current_key:
                if current_key == 'Options':
                    question[current_key] = current_value
                else:
                    question[current_key] = ' '.join(current_value)

            
            # Ensure we have exactly 4 options
            if 'Options' not in question or len(question.get('Options', [])) != 4:
                # Use default options in German if we don't have exactly 4
                question['Options'] = [
                    "Pizza essen",
                    "Einen Burger essen",
                    "Salat essen",
                    "Pasta essen"
                ]
            return question
        except Exception as e:
            print(f"Error parsing generated question: {str(e)}")
            return None

    def get_feedback(self, question: Dict, selected_answer: int) -> Dict:
        """Generate feedback for the selected answer for a Goethe B1 listening
        comprehension question"""
        if not question or 'Options' not in question:
            return None

        # Erstelle den Prompt zur Generierung von Feedback
        prompt = f"""
            Gegeben diese Goethe B1 Hörverständnisfrage und die ausgewählte
            Antwort, gib bitte ein Feedback, das erklärt, ob die Antwort korrekt
            ist und warum. Halte die Erklärung klar und präzise.
        """
        if 'Introduction' in question:
            prompt += f"Einleitung: {question['Introduction']}\n"
            prompt += f"Unterhaltung: {question['Conversation']}\n"
        else:
            prompt += f"Situation: {question['Situation']}\n"

        prompt += f"Frage: {question['Question']}\n"
        prompt += "Antwortmöglichkeiten:\n"
        for i, opt in enumerate(question['Options'], 1):
            prompt += f"{i}. {opt}\n"

        prompt += f"\nAusgewählte Antwort: {selected_answer}\n"
        prompt += "\nGib bitte Feedback im JSON-Format mit den folgenden Feldern an:\n"
        prompt += "- correct: true/false\n"
        prompt += "- explanation: kurze Erklärung, warum die Antwort korrekt oder nicht korrekt ist\n"
        prompt += "- correct_answer: die Nummer der korrekten Antwort (1-4)\n"

        # Get feedback
        response = self._invoke_bedrock(prompt)
        if not response:
            return None

        try:
            # Parse the JSON response
            feedback = json.loads(response.strip())
            return feedback
        except:
            # If JSON parsing fails, return a basic response with a default correct answer
            return {
                "correct": False,
                "explanation": "Unable to generate detailed feedback. Please try again.",
                "correct_answer": 1  # Default to first option
            }
