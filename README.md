# Streamlit Chat Test Suite (Streamlit Frontend)
A lightweight Streamlit UI to interact with a backend streaming chat endpoint. It supports:
- Chat only
- Chat with RAG
- Document generation

The app streams Server-Sent Events (SSE) from a single endpoint and displays assistant tokens as they arrive.


## Prerequisites
- Python 3.12+
- virtualenv (or Python’s built-in venv)
- Internet access to fetch Python dependencies
- A running backend that exposes a streaming chat endpoint compatible with the app
- Optional: Docker (if you prefer containerized runs)

## Quick Start (Local)
1. Create and activate a virtual environment:

- macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate

- Windows (PowerShell):
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

2. Install dependencies:
pip install --upgrade pip
pip install -r requirements.txt

3. Set environment variables:

- Required:
    - CHAT_STREAM_URL: URL of your backend SSE chat stream (e.g., [http://localhost:8000/api/v1/chat/stream](http://localhost:8000/api/v1/chat/stream))

- Optional:
    - AZURE_AD_TOKEN: Bearer token if your backend requires Azure AD auth

You can either export them directly or load from the provided .env file (update its values first).

4. Run the app:
streamlit run app.py

1. Open the UI:

- Streamlit will print a local URL (typically [http://localhost:8501](http://localhost:8501)). Open it in your browser.

## Running with Docker
1. Build the image:
    docker build -t streamlit-frontend:v1 .

2. Run the container:

   - If your backend runs on your host, you can use host.docker.internal to reach it from the container (Docker Desktop on macOS/Windows). On Linux, consider using the host IP or a user-defined network.
    #### Using .env file (recommended)
    docker run --rm -p 8501:8501 --env-file .env streamlit-frontend:v1

3. Open [http://localhost:8501](http://localhost:8501) in your browser.

## Using the App
    - Mode: Choose between “Chat only”, “Chat with RAG”, or “Document gen”. The selection is sent as a control hint to your backend to toggle behavior.
    - Sessions:
        - Create a new session with a title.
        - Switch between sessions in the left pane.
        - Delete a selected session to remove it from the list.

    - Chat:
        - Type your message in the chat input.
        - The response streams in real-time; only “answer” tokens are displayed when mixed payloads are received.

## Troubleshooting
- Blank page or cannot connect:
    - Ensure your backend is running and reachable from where the frontend runs.
    - Verify CHAT_STREAM_URL is correct and accessible (CORS not required for SSE in this context, but network/firewall rules still apply).

- 401/403 errors:
    - Set a valid AZURE_AD_TOKEN if your backend requires it.
    - Check token expiry and audience (aud) claims.

- Port conflicts on 8501:
    - Stop any process occupying the port or run Streamlit on a different port:
    streamlit run app.py --server.port=8600

- Docker cannot reach host backend:
    - On macOS/Windows, use [http://host.docker.internal](http://host.docker.internal).
    - On Linux, use your host’s IP or attach both containers to a user-defined Docker network and use service names.

## License
This project is intended for internal testing and demonstration. Apply your organization’s licensing policies as appropriate.
