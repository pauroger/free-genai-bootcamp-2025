# Running Ollama Third-Party Service

## Choosing a Model

You can get the model_id that ollama will launch from the [Ollama Library](https://ollama.com/library).

## German Chat Tutor App

A Streamlit-based application that provides an interactive German language tutor powered by LLM technology.

### Technology Stack

- Frontend: Streamlit web interface
- Backend: FastAPI microservice architecture
- LLM Integration: Llama 3.2 via Ollama
- API Protocol: Server-Sent Events (SSE) for streaming responses
- Communication: Asynchronous HTTP with aiohttp
- Service Orchestration: Custom MicroService and ServiceOrchestrator classes

### Architecture

The system consists of two main components:

Streamlit Frontend:

- Handles user interaction
- Manages chat history
- Streams responses from the backend
 -Provides tutor configuration options

FastAPI Microservice Backend:

- Manages LLM service connections
- Processes chat completion requests
- Orchestrates service communication
- Supports streaming responses

### How It Works

Users interact with a chat interface where they can practice writing in German
The system processes user input through a specialized German tutor LLM
The tutor responds with:

- Corrections to grammar and vocabulary
- Explanations of language rules
- Encouragement to continue practicing
- Follow-up questions to maintain conversation flow

The chat history is maintained throughout the session.
