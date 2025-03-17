import json
from duckduckgo_search import DDGS
import requests
from html2text import HTML2Text
from dotenv import load_dotenv
import os
import re
from openai import OpenAI


# Config
def load_env():
    load_dotenv(dotenv_path=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".env"
    ))

    return os.getenv("OPENAI_API_KEY")


def sanitize_filename(filename):
    """Remove or replace characters that aren't suitable for filenames"""
    # Replace spaces and special characters
    sanitized = re.sub(r'[^\w\s-]', '', filename)
    # Replace spaces with underscores
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized.lower()


def search_web(query: str) -> str:
    results = DDGS().text(query, max_results=5)
    if results:
        return [
            {
                "title": result["title"],
                "url": result["href"],
            }
            for result in results
        ]
    return []


def make_json_safe(text):
    """Sanitize text to make it safe for JSON inclusion"""
    if text is None:
        return ""
    
    try:
        # First try to use JSON's own escaping mechanism
        # This will handle most escaping issues properly
        return json.dumps(text)[1:-1]  # Remove the surrounding quotes
    except Exception:
        # If that fails, fall back to manual character replacement
        replacements = {
            '\b': '\\b',
            '\f': '\\f',
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
            '\\': '\\\\',
            '"': '\\"'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
            
        # Remove other control characters
        text = ''.join(c for c in text if ord(c) >= 32 or c in ['\n', '\r', '\t'])
        
        return text


def safe_json_parse(text):
    """
    Safely parse JSON from text that might contain non-JSON elements.
    Returns a dictionary on success, None on failure.
    """
    import json
    import re
    
    # Try multiple cleaning strategies
    cleaning_strategies = [
        # Strategy 1: As is
        lambda t: t,
        # Strategy 2: Remove markdown code blocks
        lambda t: re.sub(r'```(?:json)?(.*?)```', r'\1', t, flags=re.DOTALL).strip(),
        # Strategy 3: Find the first { and last }
        lambda t: t[t.find('{'):t.rfind('}')+1] if '{' in t and '}' in t else t,
        # Strategy 4: Fix common JSON issues
        lambda t: t.replace('\\"', '"').replace('\\\\', '\\'),
        # Strategy 5: Extract only what appears to be JSON
        lambda t: re.search(r'(\{.*\})', t, re.DOTALL).group(1) if re.search(r'(\{.*\})', t, re.DOTALL) else t
    ]
    
    for strategy in cleaning_strategies:
        try:
            cleaned = strategy(text)
            return json.loads(cleaned)
        except (json.JSONDecodeError, AttributeError):
            continue
    
    return None


def get_page_content(url: str) -> str:
    try:
        response = requests.get(url)
        h = HTML2Text()
        h.ignore_links = False
        h.body_width = 0  # Don't wrap text
        h.ignore_images = True
        
        content = h.handle(response.text)
        
        # Try to extract lyrics specifically if it's a known lyrics site
        raw_content = content
        if "genius.com" in url:
            # Simple extraction for Genius lyrics
            lyrics_section = re.search(r'Lyrics(.+?)(?:Embed|Translations|About|More on Genius)', 
                                      content, re.DOTALL | re.IGNORECASE)
            if lyrics_section:
                raw_content = lyrics_section.group(1).strip()
        
        # Limit content length for JSON
        limited_content = raw_content[:4000] if len(raw_content) > 4000 else raw_content
        
        # Return the processed content
        return limited_content
    except Exception as e:
        print(f"Error fetching content from {url}: {str(e)}")
        return f"Error fetching content: {str(e)}"


def extract_vocabulary(text: str) -> list:
    words = set(text.lower().split())
    vocabulary = [word for word in words if word.isalpha()]
    return sorted(vocabulary)


def parse_lyrics(text: str) -> list:
    """Better parsing to extract song lyrics from text content."""
    # Split by newline and filter empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Clean up the lines
    cleaned_lines = []
    for line in lines:
        # Skip HTML tags, metadata, and section markers 
        if line.startswith('<') and line.endswith('>'):
            continue
        if line.startswith('[') and line.endswith(']'):
            continue
        if line.lower().startswith(('intro', 'verse', 'chorus', 'bridge', 'outro')):
            continue
        if any(term in line.lower() for term in ['embed', 'contribute', 'lyrics', 'translation']):
            continue
        
        cleaned_lines.append(line)
    
    return cleaned_lines


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
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Initialize the results dictionary
    results_data = {
        "search_results": [],
        "get_page_content": {
            "url": "",
            "content": ""
        },
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
                title, search for the song lyrics online, then get the full lyrics text
                from a reliable lyrics website, and finally extract vocabulary from the lyrics.
                
                You must follow these exact steps in order:
                1. Search for the song lyrics using the search_web tool
                2. Find a good lyrics website from the search results (e.g., genius.com, lyrics.com)
                3. Retrieve the full lyrics using the get_page_content tool
                4. Extract the vocabulary by calling the extract_vocabulary tool with the FULL LYRICS text
                5. Return your analysis in JSON format
                
                Explain the meaning of new words in simple terms and provide
                example sentences. Use the user's native language to explain the
                meaning of new words. Focus on words that would be valuable for a
                language learner.

                YOUR RESPONSE MUST BE VALID JSON. Do not include markdown
                formatting, code blocks, or any text before or after the JSON.

                Return your response as a single JSON object with this exact structure:
                {{
                    "vocabulary_list": [
                        {{
                            "word": "word1",
                            "meaning": "meaning in {user_language}",
                            "example": "example sentence in {foreign_language}"
                        }},
                        ...more words...
                    ],
                    "intent": "Explanation of what the song portrays, including themes and summary"
                }}

                The user's native language is {user_language}. The
                language of the foreign song the user is learning is
                {foreign_language}.

                IMPORTANT RULES FOR JSON FORMATTING:
                1. Ensure all special characters are properly escaped in your JSON response
                2. All strings must be enclosed in double quotes
                3. Double quotes within strings must be escaped with a backslash
                4. Backslashes must be escaped with another backslash
                5. Do not include any characters like backticks or markdown formatting
                6. Return pure, valid JSON only - no text before or after
            """,
        },
        {
            "role": "user",
            "content": f"help me learn about the song '{song_title}'",
        },
    ]

    goal_achieved = False
    limit = 10
    raw_text_content = ""

    while not goal_achieved and len(messages) < limit:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            response_format={"type": "json_object"},  # Request JSON format explicitly
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
                    raw_content = get_page_content(url)
                    print(f'Calling get_page_content "{url}"')
                    results_data["get_page_content"]["url"] = url
                    
                    # Store the raw content for later lyrics extraction
                    raw_text_content = raw_content
                    
                    # Try to extract lyrics directly
                    extracted_lyrics = parse_lyrics(raw_content)
                    if extracted_lyrics:
                        results_data["extract_vocabulary"]["lyrics"] = extracted_lyrics
                        print(f"Directly extracted {len(extracted_lyrics)} lyrics lines")
                    
                    # Store JSON-safe content
                    results_data["get_page_content"]["content"] = make_json_safe(raw_content)

                elif tool_call.function.name == "extract_vocabulary":
                    text = arguments["text"]
                    
                    # Extract lyrics from this text if we don't have them yet
                    if not results_data["extract_vocabulary"]["lyrics"]:
                        lyrics = parse_lyrics(text)
                        results_data["extract_vocabulary"]["lyrics"] = lyrics
                        print(f"Extracted {len(lyrics)} lyrics lines from vocabulary text")
                    
                    # Extract words
                    word_list = extract_vocabulary(text)
                    results_data["extract_vocabulary"]["words"] = word_list
                    
                    print(f'Calling extract_vocabulary "{text[:50]}..."')
                    for i, word in enumerate(word_list[:10]):
                        print(f"  - {word}")
                    if len(word_list) > 10:
                        print(f"  ... and {len(word_list)-10} more words")
                    
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

            # You can also keep the console output if desired
            print(f"Logged response for '{song_title}' to log.txt")
            try:
                # Try to parse the response as JSON
                # First clean the response in case it has markdown or other non-JSON content
                cleaned_response = final_response
                
                # Remove markdown code block markers if present
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response.replace("```json", "", 1)
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response.replace("```", "", 1)
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response.rsplit("```", 1)[0]
                    
                # Strip whitespace
                cleaned_response = cleaned_response.strip()
                
                # Try to parse JSON using the safe parser
                response_data = safe_json_parse(cleaned_response)
                
                if response_data:
                    # Extract vocabulary list and intent
                    if "vocabulary_list" in response_data:
                        results_data["extract_vocabulary"]["vocabulary_list"] = response_data["vocabulary_list"]
                    if "intent" in response_data:
                        results_data["intent"] = response_data["intent"]
                else:
                    raise json.JSONDecodeError("Failed to parse JSON with safe parser", cleaned_response, 0)
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Failed to parse response: {final_response[:100]}...")
                
                # Save the problematic response for debugging
                os.makedirs('songs', exist_ok=True)
                with open(f'songs/{sanitize_filename(song_title)}_error_response.txt', 'w', encoding='utf-8') as f:
                    f.write(final_response)
                
                # Alternative: Create a simple default structure to avoid breaking the app
                results_data["extract_vocabulary"]["vocabulary_list"] = []
                results_data["intent"] = f"Error parsing response for '{song_title}'. Please try again."
                
                # If the response is not valid JSON, try to extract information manually
                import re
                
                # Look for vocabulary list with regex patterns
                # Try multiple patterns to increase chances of extraction
                vocab_patterns = [
                    # Original pattern
                    r'(\d+)\.\s+\*\*([^*]+)\*\*\s+\([^)]+\)\s+\-\s+\*Meaning:\*\s+([^\n]+)\s+\-\s+\*Example:\*\s+([^\n]+)',
                    # Simplified pattern
                    r'"word"\s*:\s*"([^"]+)"\s*,\s*"meaning"\s*:\s*"([^"]+)"\s*,\s*"example"\s*:\s*"([^"]+)"',
                    # Another variation
                    r'word["\']?\s*:\s*["\']([^"\']+)["\'].*?meaning["\']?\s*:\s*["\']([^"\']+)["\'].*?example["\']?\s*:\s*["\']([^"\']+)["\']'
                ]
                
                vocab_list = []
                for pattern in vocab_patterns:
                    items = re.findall(pattern, final_response, re.DOTALL)
                    if items:
                        for item in items:
                            if len(item) == 3:  # patterns with 3 groups
                                word, meaning, example = item
                                vocab_list.append({
                                    "word": word.strip(),
                                    "meaning": meaning.strip(),
                                    "example": example.strip()
                                })
                            elif len(item) == 4:  # patterns with 4 groups (including index)
                                _, word, meaning, example = item
                                vocab_list.append({
                                    "word": word.strip(),
                                    "meaning": meaning.strip(),
                                    "example": example.strip()
                                })
                
                if vocab_list:
                    results_data["extract_vocabulary"]["vocabulary_list"] = vocab_list
                
                # Look for intent/summary section with multiple patterns
                intent_patterns = [
                    r'(?:Summary of Themes|intent)[^\n]*\n((?:.+\n?)+)',
                    r'"intent"\s*:\s*"([^"]+)"',
                    r'intent["\']?\s*:\s*["\']([^"\']+)["\']'
                ]
                
                for pattern in intent_patterns:
                    summary_match = re.search(pattern, final_response, re.DOTALL)
                    if summary_match:
                        results_data["intent"] = summary_match.group(1).strip()
                        break  # Break to exit loop once a match is found
                        
            goal_achieved = True
    
    # Last chance to extract lyrics if we still don't have them
    if not results_data["extract_vocabulary"]["lyrics"] and raw_text_content:
        last_chance_lyrics = parse_lyrics(raw_text_content)
        if last_chance_lyrics:
            results_data["extract_vocabulary"]["lyrics"] = last_chance_lyrics
            print(f"Last-chance extraction found {len(last_chance_lyrics)} lyrics lines")
    
    # Save results to JSON file with improved error handling
    try:
        # Use the sanitized filename
        safe_filename = sanitize_filename(song_title)
        
        # First verify we can serialize to JSON
        # Use ensure_ascii=True for maximum compatibility
        json_str = json.dumps(results_data, ensure_ascii=True, indent=2)
        
        # Save to file
        os.makedirs('songs', exist_ok=True)
        with open(f'songs/{safe_filename}_song_analysis.json', 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        print(f"Results saved to songs/{safe_filename}_song_analysis.json")
        
        return results_data
    except Exception as e:
        error_msg = f"Error saving results: {str(e)}"
        print(error_msg)
        
        # Create emergency backup with simplified content
        emergency_data = {
            "search_results": results_data["search_results"],
            "extract_vocabulary": {
                "lyrics": results_data["extract_vocabulary"]["lyrics"],
                "words": results_data["extract_vocabulary"]["words"],
                "vocabulary_list": results_data["extract_vocabulary"]["vocabulary_list"]
            },
            "intent": results_data["intent"],
            "get_page_content": {
                "url": results_data["get_page_content"]["url"],
                "content": "Content removed due to JSON error"
            }
        }
        
        # Try to save the emergency version
        try:
            with open(f'songs/{safe_filename}_emergency.json', 'w', encoding='utf-8') as f:
                json.dump(emergency_data, f, ensure_ascii=True)
            print(f"Emergency backup saved to songs/{safe_filename}_emergency.json")
            return emergency_data
        except Exception as e2:
            print(f"Emergency save also failed: {str(e2)}")
            raise e 


if __name__ == "__main__":
    song_title = input("Enter a song title: ")
    user_language = input("Enter your language (default: English): ") or "English"
    foreign_language = input("Enter the song language (default: German): ") or "German"
    
    run_language_tutor(song_title, user_language, foreign_language)
