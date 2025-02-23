from typing import Optional, Dict, List
import boto3
import os


# MODEL_ID = "amazon.titan-text-lite-v1" # Getting errors sometimes because the Max input tokens is: 4096
# MODEL_ID = "amazon.titan-text-express-v1" # Misses a bunch of stuff from the transcript.
MODEL_ID = "mistral.mistral-7b-instruct-v0:2" # Pretty results!!

# Other enabled models:
# MODEL_ID = "mistral.mixtral-8x7b-instruct-v0:1"
# MODEL_ID = "mistral.mistral-large-2402-v1:0"
# MODEL_ID = "meta.llama3-2-1b-instruct-v1:0"
# MODEL_ID = "meta.llama3-2-3b-instruct-v1:0"

VIDEO_ID = "J6B82SjPFYY"

class TranscriptStructurer:
    def __init__(self, model_id: str = MODEL_ID):
        # Initialize Bedrock client
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="eu-west-1")
        self.model_id = model_id
        self.prompts = {
            1: """
                Extract and structure section 'Teil 1' from this transcript.

                Instructions:
                - This section contains an example followed by 5 texts.
                - For each text, generate 3 True or False statements that relate to the content of that text.

                Format for each text:
                <Text>
                Statement 1: [True/False]
                Statement 2: [True/False]
                Statement 3: [True/False]
            """,
            2: """
                Extract and structure section 'Teil 2' from this transcript.

                Instructions:
                - Generate 5 questions based solely on the conversation.
                - Each question must have 3 possible answers, with only one correct answer.

                Format for each question:
                <question>
                Question: [question text]
                Options:
                1. [option 1]
                2. [option 2]
                3. [option 3]
                Answer: [correct option number]
                </question>
            """,
            3: """
                Extract and structure section 'Teil 3' from this transcript.

                Instructions:
                - Generate 6 True or False statements that are directly supported by the transcript.

                Format for each statement:
                <statement>
                Text: [statement text]
                Answer: [True/False]
                </statement>
            """,
            4: """
                Extract and structure section 'Teil 4' from this transcript.

                Instructions:
                - Generate 8 statements.
                - For each statement, indicate which of the 3 participants in the conversation said it.

                Format for each statement:
                <statement>
                Text: [statement text]
                Speaker: [Name or identifier of the speaker]
                </statement>
            """
        }

    def _invoke_bedrock(self, prompt: str, transcript: str) -> Optional[str]:
        full_prompt = f"{prompt}\n\nHere's the transcript:\n{transcript}"
        messages = [{
            "role": "user",
            "content": [{"text": full_prompt}]
        }]
        try:
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={"temperature": 0}
            )
            return response['output']['message']['content'][0]['text']
        except Exception as e:
            print(f"Error invoking Bedrock: {str(e)}")
            return None

    def structure_transcript(self, transcript: str) -> Dict[int, str]:
        results = {}
        # Process all 4 sections (Teil 1 to Teil 4)
        for section_num in range(1, 5):
            result = self._invoke_bedrock(self.prompts[section_num], transcript)
            if result:
                results[section_num] = result
        return results

    def save_questions(self, structured_sections: Dict[int, str], base_filename: str) -> bool:
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(base_filename), exist_ok=True)
            for section_num, content in structured_sections.items():
                filename = f"{os.path.splitext(base_filename)[0]}_teil{section_num}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
            return True
        except Exception as e:
            print(f"Error saving structured sections: {str(e)}")
            return False

    def load_transcript(self, filename: str) -> Optional[str]:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading transcript: {str(e)}")
            return None

if __name__ == "__main__":
    structurer = TranscriptStructurer()
    transcript = structurer.load_transcript(f"./data/transcripts/{VIDEO_ID}.txt")
    if transcript:
        structured_sections = structurer.structure_transcript(transcript)
        structurer.save_questions(structured_sections, f"./data/questions/{VIDEO_ID}.txt")
