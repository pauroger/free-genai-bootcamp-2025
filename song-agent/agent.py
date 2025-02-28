import json
from openai import OpenAI
from duckduckgo_search import DDGS
import requests
from html2text import HTML2Text
from dotenv import load_dotenv
import os

# config
load_dotenv(dotenv_path=os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".env"
))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


client = OpenAI(api_key=OPENAI_API_KEY)


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


user_language = "English"
foreign_language = "German"
song_title = "Die Philosoffen"
messages = [
    {
        "role": "system",
        "content": f"""
            You are a helpful language tutor. 
            When the user provides a song title, search for the song lyrics and help them learn new vocabulary from it. 
            First search for the lyrics, then extract vocabulary from them. 
            Explain the meaning of new words in simple terms and provide example sentences. 
            Use the user's native language to explain the meaning of new words.
            Focus on words that would be valuable for a language learner.
            The user's native language is {user_language}.
            The language of the foreign song the user is learning is {foreign_language}.
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
                result = search_web(arguments["query"])
                print(f'Calling search_web "{arguments["query"]}"')
                for item in result:
                    print(f'  - "{item["title"]}"')

            elif tool_call.function.name == "get_page_content":
                result = get_page_content(arguments["url"])
                print(f'Calling get_page_content "{arguments["url"]}"')

            elif tool_call.function.name == "extract_vocabulary":
                result = extract_vocabulary(arguments["text"])
                print(f'Calling extract_vocabulary "{arguments["text"]}"')
                for word in result:
                    print(f"  - {word}")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                }
            )
    else:
        goal_achieved = True

print(messages[-1].content)
