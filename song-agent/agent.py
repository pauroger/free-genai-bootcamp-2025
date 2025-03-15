import json
from duckduckgo_search import DDGS
import requests
from html2text import HTML2Text
from dotenv import load_dotenv
import os
import openai


# config
def load_env():
    load_dotenv(dotenv_path=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".env"
    ))

    return os.getenv("OPENAI_API_KEY")


def search_web(query: str) -> str:
    results = DDGS().text(query, max_results=10)
    if results:
        return [
            {
                "title": result["title"],
                "url": result["href"],
            }
            for result in results
        ]
    return []


def get_page_content(url: str) -> str:
    response = requests.get(url)
    h = HTML2Text()
    h.ignore_links = False
    content = h.handle(response.text)
    return content[:4000] if len(content) > 4000 else content


def extract_vocabulary(text: str) -> list:
    words = set(text.lower().split())
    vocabulary = [word for word in words if word.isalpha()]
    return sorted(vocabulary)


def parse_lyrics(text: str) -> list:
    # Simple parsing to get the lines of the lyrics
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    # Remove any non-lyric lines (like title)
    if lines and lines[0] == "Die Philosoffen":
        lines = lines[1:]
    return lines


def run_language_tutor(song_title, user_language="English", foreign_language="German"):
    """
    Run the language tutor agent to analyze a song and return the results.
    
    Args:
        song_title (str): The title of the song to analyze
        user_language (str): The user's native language
        foreign_language (str): The language of the song
        
    Returns:
        dict: The analysis results in JSON format
    """
    OPENAI_API_KEY = load_env()
    client = openai.api_key =OPENAI_API_KEY
    
    # Initialize the results dictionary
    results_data = {
        "search_results": [],
        "get_page_content": "",
        "extract_vocabulary": {
            "lyrics": [],
            "words": [],
            "vocabulary_list": []
        },
        "intent": ""
    }
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the web for information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query to search the web for.",
                        },
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_page_content",
                "description": "Get the content of a web page.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL of the web page.",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "extract_vocabulary",
                "description": "Extract new vocabulary from a text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to extract new vocabulary from.",
                        },
                    },
                    "required": ["text"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
    ]

    messages = [
        {
            "role": "system",
            "content": f"""
                You are a helpful language tutor. When the user provides a song
                title, search for the song lyrics and help them learn new vocabulary
                from it. First search for the lyrics, then extract vocabulary from
                them. Explain the meaning of new words in simple terms and provide
                example sentences. Use the user's native language to explain the
                meaning of new words. Focus on words that would be valuable for a
                language learner.

                Format your response as a JSON object with the following structure:
                {{
                    "vocabulary_list": [
                        {{
                            "word": "word1",
                            "meaning": "meaning in {user_language}",
                            "example": "example sentence in {user_language}"
                        }},
                        // more words...
                    ],
                    "intent": "Explanation of what the song portrays, including themes and summary"
                }}

                The user's native language is {user_language}. The
                language of the foreign song the user is learning is
                {foreign_language}.
            """,
        },
        {
            "role": "user",
            "content": f"help me learn about the song '{song_title}'",
        },
    ]

    goal_achieved = False
    limit = 10

    while not goal_achieved and len(messages) < limit:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
        )

        messages.append(completion.choices[0].message)

        if completion.choices[0].message.tool_calls:
            for tool_call in completion.choices[0].message.tool_calls:
                arguments = json.loads(tool_call.function.arguments)

                if tool_call.function.name == "search_web":
                    query = arguments["query"]
                    result = search_web(query)
                    print(f'Calling search_web "{query}"')
                    results_data["search_results"] = result
                    for item in result:
                        print(f'  - "{item["title"]}"')

                elif tool_call.function.name == "get_page_content":
                    url = arguments["url"]
                    result = get_page_content(url)
                    print(f'Calling get_page_content "{url}"')
                    results_data["get_page_content"] = {
                        "url": url,
                        "content": result
                    }

                elif tool_call.function.name == "extract_vocabulary":
                    text = arguments["text"]
                    # Parse lyrics and store them
                    lyrics = parse_lyrics(text)
                    results_data["extract_vocabulary"]["lyrics"] = lyrics
                    
                    # Extract words
                    word_list = extract_vocabulary(text)
                    results_data["extract_vocabulary"]["words"] = word_list
                    
                    print(f'Calling extract_vocabulary "{text[:50]}..."')
                    for word in word_list:
                        print(f"  - {word}")
                    
                    result = word_list

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                    }
                )
        else:
            # Get the LLM's final response which should contain the vocabulary list and intent
            final_response = completion.choices[0].message.content
            
            try:
                # Try to parse the response as JSON
                response_data = json.loads(final_response)
                
                # Extract vocabulary list and intent
                if "vocabulary_list" in response_data:
                    results_data["extract_vocabulary"]["vocabulary_list"] = response_data["vocabulary_list"]
                if "intent" in response_data:
                    results_data["intent"] = response_data["intent"]
            except json.JSONDecodeError:
                # If the response is not valid JSON, try to extract information manually
                import re
                
                # Look for vocabulary list with regex patterns
                vocab_items = re.findall(r'(\d+)\.\s+\*\*([^*]+)\*\*\s+\([^)]+\)\s+\-\s+\*Meaning:\*\s+([^\n]+)\s+\-\s+\*Example:\*\s+([^\n]+)', final_response)
                
                vocab_list = []
                for _, word, meaning, example in vocab_items:
                    vocab_list.append({
                        "word": word.strip(),
                        "meaning": meaning.strip(),
                        "example": example.strip()
                    })
                
                results_data["extract_vocabulary"]["vocabulary_list"] = vocab_list
                
                # Look for intent/summary section
                summary_match = re.search(r'(?:Summary of Themes|intent)[^\n]*\n((?:.+\n?)+)', final_response)
                if summary_match:
                    results_data["intent"] = summary_match.group(1).strip()
            
            goal_achieved = True

    # Save results to JSON file
    os.makedirs('songs', exist_ok=True)
    with open(f'songs/{song_title}_song_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)

    print(f"Results saved to songs/{song_title}_song_analysis.json")
    
    return results_data


if __name__ == "__main__":
    # For testing purposes
    song_title = input("Enter a song title: ")
    user_language = input("Enter your language (default: English): ") or "English"
    foreign_language = input("Enter the song language (default: German): ") or "German"
    
    run_language_tutor(song_title, user_language, foreign_language)
