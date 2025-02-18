import chromadb
from chromadb.utils import embedding_functions
import json
import boto3
from typing import Dict, List, Optional
import os
import re
import glob

MODEL_ID = "amazon.titan-embed-text-v2:0" 

class BedrockEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, model_id=MODEL_ID):
        """Initialize Bedrock embedding function (using region eu-west-1)"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="eu-west-1")
        self.model_id = model_id

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using Bedrock"""
        embeddings = []
        for text in texts:
            try:
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps({
                        "inputText": text
                    })
                )
                response_body = json.loads(response['body'].read())
                embedding = response_body['embedding']
                embeddings.append(embedding)
            except Exception as e:
                print(f"Error generating embedding: {str(e)}")
                # Return a zero vector as fallback; Titan model uses 1536 dimensions
                embeddings.append([0.0] * 1536)
        return embeddings

class QuestionVectorStore:
    def __init__(self, persist_directory: str = "backend/data/vectorstore"):
        """Initialize the vector store for Goethe B1 listening exercises (Sections 1-4)"""
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use Bedrock embedding function
        self.embedding_fn = BedrockEmbeddingFunction()
        
        # Create or get collections for each section type
        self.collections = {
            "section1": self.client.get_or_create_collection(
                name="section1_questions",
                embedding_function=self.embedding_fn,
                metadata={"description": "Goethe B1 listening exercises - Section 1 (True/False statements about texts)"}
            ),
            "section2": self.client.get_or_create_collection(
                name="section2_questions",
                embedding_function=self.embedding_fn,
                metadata={"description": "Goethe B1 listening comprehension questions - Section 2 (Multiple-choice questions)"}
            ),
            "section3": self.client.get_or_create_collection(
                name="section3_questions",
                embedding_function=self.embedding_fn,
                metadata={"description": "Goethe B1 listening exercises - Section 3 (True/False statements)"}
            ),
            "section4": self.client.get_or_create_collection(
                name="section4_questions",
                embedding_function=self.embedding_fn,
                metadata={"description": "Goethe B1 listening exercises - Section 4 (Speaker identification)"}
            )
        }

    def add_questions(self, section_num: int, questions: List[Dict], video_id: str):
        """Add questions to the vector store for sections 1-4"""
        if section_num not in [1, 2, 3, 4]:
            raise ValueError("Only sections 1, 2, 3, and 4 are supported")
            
        collection = self.collections[f"section{section_num}"]
        
        ids = []
        documents = []
        metadatas = []
        
        for idx, question in enumerate(questions):
            # Create a unique ID for each question
            question_id = f"{video_id}_{section_num}_{idx}"
            ids.append(question_id)
            
            # Store the full question structure as metadata
            metadatas.append({
                "video_id": video_id,
                "section": section_num,
                "question_index": idx,
                "full_structure": json.dumps(question)
            })
            
            # Create a searchable document based on section type
            if section_num == 1:
                # Section 1: Text with associated True/False statements
                document = f"Text: {question.get('Text', '')}\nStatements: {', '.join(question.get('Statements', []))}"
            elif section_num == 2:
                # Section 2: Listening comprehension multiple-choice question
                document = (
                    f"Introduction: {question.get('Introduction', '')}\n"
                    f"Conversation: {question.get('Conversation', '')}\n"
                    f"Question: {question.get('Question', '')}\n"
                    f"Options: {', '.join(question.get('Options', []))}"
                )
            elif section_num == 3:
                # Section 3: True/False statements exercise
                document = (
                    f"Situation: {question.get('Situation', '')}\n"
                    f"Question: {question.get('Question', '')}\n"
                    f"Statements: {', '.join(question.get('Statements', []))}"
                )
            elif section_num == 4:
                # Section 4: Speaker identification task
                document = (
                    f"Statement: {question.get('Statement', '')}\n"
                    f"Options: {', '.join(question.get('Options', []))}"
                )
            documents.append(document)
        
        # Add to collection
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def search_similar_questions(
        self, 
        section_num: int, 
        query: str, 
        n_results: int = 5
    ) -> List[Dict]:
        """Search for similar questions in the vector store for sections 1-4"""
        if section_num not in [1, 2, 3, 4]:
            raise ValueError("Only sections 1, 2, 3, and 4 are supported")
            
        collection = self.collections[f"section{section_num}"]
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Convert results to a more usable format
        questions = []
        for idx, metadata in enumerate(results['metadatas'][0]):
            question_data = json.loads(metadata['full_structure'])
            question_data['similarity_score'] = results['distances'][0][idx]
            questions.append(question_data)
            
        return questions

    def get_question_by_id(self, section_num: int, question_id: str) -> Optional[Dict]:
        """Retrieve a specific question by its ID for sections 1-4"""
        if section_num not in [1, 2, 3, 4]:
            raise ValueError("Only sections 1, 2, 3, and 4 are supported")
            
        collection = self.collections[f"section{section_num}"]
        
        result = collection.get(
            ids=[question_id],
            include=['metadatas']
        )
        
        if result['metadatas']:
            return json.loads(result['metadatas'][0]['full_structure'])
        return None

    def parse_questions_from_file(self, filename: str) -> List[Dict]:
        """Parse questions from a structured text file.
           Supports keys:
             - For Section 1: 'Text:' and 'Statements:'
             - For Section 2: 'Introduction:', 'Conversation:', 'Question:', 'Options:'
             - For Section 3: 'Situation:', 'Question:', 'Statements:'
             - For Section 4: 'Statement:' and 'Options:'
        """
        questions = []
        current_question = {}
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith('<question>'):
                    current_question = {}
                elif line.startswith('Text:'):
                    i += 1
                    if i < len(lines):
                        current_question['Text'] = lines[i].strip()
                elif line.startswith('Statements:'):
                    statements = []
                    i += 1
                    # Read until an empty line or a line that looks like a new key or end tag
                    while i < len(lines):
                        next_line = lines[i].strip()
                        if not next_line or next_line.endswith(':') or next_line.startswith('<'):
                            break
                        # If the line starts with a digit and a dot, remove them
                        if next_line[0].isdigit() and next_line[1] == '.':
                            statements.append(next_line[2:].strip())
                        else:
                            statements.append(next_line)
                        i += 1
                    current_question['Statements'] = statements
                    continue  # skip the increment at the end of loop
                elif line.startswith('Introduction:'):
                    i += 1
                    if i < len(lines):
                        current_question['Introduction'] = lines[i].strip()
                elif line.startswith('Conversation:'):
                    i += 1
                    if i < len(lines):
                        current_question['Conversation'] = lines[i].strip()
                elif line.startswith('Situation:'):
                    i += 1
                    if i < len(lines):
                        current_question['Situation'] = lines[i].strip()
                elif line.startswith('Question:'):
                    i += 1
                    if i < len(lines):
                        current_question['Question'] = lines[i].strip()
                elif line.startswith('Statement:'):
                    i += 1
                    if i < len(lines):
                        current_question['Statement'] = lines[i].strip()
                elif line.startswith('Options:'):
                    options = []
                    i += 1
                    while i < len(lines):
                        option_line = lines[i].strip()
                        if option_line and option_line[0].isdigit() and option_line[1] == '.':
                            options.append(option_line[2:].strip())
                        else:
                            break
                        i += 1
                    current_question['Options'] = options
                    continue
                elif line.startswith('</question>'):
                    if current_question:
                        questions.append(current_question)
                        current_question = {}
                i += 1
            return questions
        except Exception as e:
            print(f"Error parsing questions from {filename}: {str(e)}")
            return []

    def index_questions_file(self, filename: str, section_num: int):
        """Index all questions from a file into the vector store"""
        # Extract video ID from filename (assumes filename starts with the video ID)
        video_id = os.path.basename(filename).split('_section')[0]
        
        # Parse questions from file
        questions = self.parse_questions_from_file(filename)
        
        # Add to vector store if any questions were parsed
        if questions:
            self.add_questions(section_num, questions, video_id)
            print(f"Indexed {len(questions)} questions from {filename}")

if __name__ == "__main__":
    # Example usage
    store = QuestionVectorStore()

    # Automatically capture all question files in the folder
    questions_folder = "./data/questions"
    pattern = re.compile(r".*_teil(\d+)\.txt")
    question_files = []

    for file_path in glob.glob(os.path.join(questions_folder, "*.txt")):
        basename = os.path.basename(file_path)
        match = pattern.match(basename)
        if match:
            section_num = int(match.group(1))
            question_files.append((file_path, section_num))

    # Optionally, sort by section number
    question_files.sort(key=lambda x: x[1])
    
    for filename, section_num in question_files:
        if os.path.exists(filename):
            store.index_questions_file(filename, section_num)
    
    # Search for similar questions using a German query example from Section 2
    # similar = store.search_similar_questions(2, "Frage zum Geburtstag", n_results=1)
    # print(similar)
