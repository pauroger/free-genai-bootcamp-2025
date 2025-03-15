import streamlit as st
import requests
import json
import sseclient
import sys
from pathlib import Path

# Try to import the custom theme if available
try:
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from themes.streamlit_theme import apply_custom_theme
    has_custom_theme = True
except ImportError:
    has_custom_theme = False

# Set page config
st.set_page_config(
    page_title="Chat in German",
    page_icon="🦙",
    layout="wide"
)

# Apply custom theme if available
if has_custom_theme:
    apply_custom_theme(primary_color="#90cdec")

# Initialize session state for chat history
if "messages" not in st.session_state:
    # Define the system message that instructs the model to act as a German tutor
    system_message = {
        "role": "system", 
        "content": """You are a helpful and encouraging German language tutor. Your goals are:
1. Encourage users to write in German as much as possible
2. Provide structured corrections to their German, explaining grammar rules, vocabulary, and syntax in a clear way
3. Maintain a positive, encouraging tone
4. Continue the conversation with relevant questions or prompts to keep the user engaged and practicing
5. If the user writes in English, gently encourage them to try in German, but still respond helpfully
6. Use a mix of German and English in your explanations, depending on the user's apparent level

Format corrections like this:
- Original: [user's text]
- Corrected: [corrected text]
- Explanation: [brief explanation of the correction]

Always end your responses with a question or prompt to continue the conversation in German."""
    }
    
    # Add an initial greeting from the assistant
    initial_greeting = {
        "role": "assistant",
        "content": "Hallo! Ich bin dein deutscher Sprachtutor. Lass uns auf Deutsch üben! Wie geht es dir heute? (Hello! I'm your German language tutor. Let's practice in German! How are you today?)"
    }
    
    # Store messages in two separate lists - one for display, one for API calls
    st.session_state.api_messages = [system_message, initial_greeting]
    st.session_state.display_messages = [initial_greeting]
else:
    # Make sure we have both message lists
    if "api_messages" not in st.session_state:
        # Recreate the system message
        system_message = {
            "role": "system", 
            "content": """You are a helpful and encouraging German language tutor. Your goals are:
1. Encourage users to write in German as much as possible
2. Provide structured corrections to their German, explaining grammar rules, vocabulary, and syntax in a clear way
3. Maintain a positive, encouraging tone
4. Continue the conversation with relevant questions or prompts to keep the user engaged and practicing
5. If the user writes in English, gently encourage them to try in German, but still respond helpfully
6. Use a mix of German and English in your explanations, depending on the user's apparent level

Format corrections like this:
- Original: [user's text]
- Corrected: [corrected text]
- Explanation: [brief explanation of the correction]

Always end your responses with a question or prompt to continue the conversation in German."""
        }
        
        # Create API messages list with system message first
        st.session_state.api_messages = [system_message] + st.session_state.messages
        
        # Create display messages without system message
        st.session_state.display_messages = [msg for msg in st.session_state.messages if msg["role"] != "system"]

# App configuration
with st.sidebar:
    st.title("🇩🇪🇨🇭🇦🇹 Chat Tutor")
    
    # Server settings
    st.subheader("Server Settings")
    server_url = st.text_input("Server URL", "http://localhost:8000")
    
    # Model settings
    st.subheader("Model Settings")
    model = st.selectbox("Model", ["llama3.2:1b"])
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    max_tokens = st.slider("Max Tokens", min_value=10, max_value=2000, value=800, step=10)
    
    # Help section
    st.subheader("How to Use")
    st.markdown("""
    1. Try writing in German
    2. The tutor will correct your grammar and vocabulary
    3. Continue the conversation to practice
    4. If you're a beginner, you can start in English
    """)
    
    # Add a button to clear chat history
    if st.button("Clear Chat"):
        # Recreate the system message
        system_message = {
            "role": "system", 
            "content": """You are a helpful and encouraging German language tutor. Your goals are:
1. Encourage users to write in German as much as possible
2. Provide structured corrections to their German, explaining grammar rules, vocabulary, and syntax in a clear way
3. Maintain a positive, encouraging tone
4. Continue the conversation with relevant questions or prompts to keep the user engaged and practicing
5. If the user writes in English, gently encourage them to try in German, but still respond helpfully
6. Use a mix of German and English in your explanations, depending on the user's apparent level

Format corrections like this:
- Original: [user's text]
- Corrected: [corrected text]
- Explanation: [brief explanation of the correction]

Always end your responses with a question or prompt to continue the conversation in German."""
        }
        
        # Add an initial greeting from the assistant
        initial_greeting = {
            "role": "assistant",
            "content": "Hallo! Ich bin dein deutscher Sprachtutor. Lass uns auf Deutsch üben! Wie geht es dir heute? (Hello! I'm your German language tutor. Let's practice in German! How are you today?)"
        }
        
        # Reset both message lists
        st.session_state.api_messages = [system_message, initial_greeting]
        st.session_state.display_messages = [initial_greeting]
        st.rerun()

# Display chat history
st.title("German Chatting Tutor 🇩🇪🇨🇭🇦🇹")

# Display chat messages (only from display_messages list)
for message in st.session_state.display_messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Function to handle streaming response
def process_streaming_response(response):
    # Create a placeholder for streaming output
    message_placeholder = st.empty()
    full_response = ""
    
    try:
        # Handle Server-Sent Events (SSE)
        client = sseclient.SSEClient(response)
        for event in client.events():
            if event.data.startswith('{'):
                try:
                    data = json.loads(event.data)
                    if 'choices' in data and len(data['choices']) > 0:
                        # Extract the content from the delta
                        delta_content = data['choices'][0].get('delta', {}).get('content', '')
                        if delta_content:
                            full_response += delta_content
                            # Update the placeholder with the accumulated response
                            message_placeholder.write(full_response)
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        st.error(f"Error processing stream: {e}")
    
    return full_response

# User input
if prompt := st.chat_input("Schreib etwas auf Deutsch... (Write something in German...)"):
    # Add user message to chat history (both display and API lists)
    user_message = {"role": "user", "content": prompt}
    st.session_state.display_messages.append(user_message)
    st.session_state.api_messages.append(user_message)
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        # Prepare the request using api_messages which includes the system prompt
        url = f"{server_url}/v1/example-service"
        
        payload = {
            "messages": st.session_state.api_messages,
            "streaming": True,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            # Make the request with stream=True for SSE handling
            with requests.post(url, json=payload, stream=True) as response:
                if response.status_code == 200:
                    # Process the streaming response
                    full_response = process_streaming_response(response)
                    
                    # Create assistant message
                    assistant_message = {"role": "assistant", "content": full_response}
                    
                    # Update both message lists
                    st.session_state.display_messages.append(assistant_message)
                    st.session_state.api_messages.append(assistant_message)
                else:
                    error_msg = f"Error: {response.status_code} - {response.text}"
                    st.error(error_msg)
        except Exception as e:
            st.error(f"Failed to connect to the server: {e}")

# Add a footer
st.markdown("---")
st.markdown("Powered by Llama 3.2 • German Language Tutor")