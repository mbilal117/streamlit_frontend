import json
import os
import uuid
import time
from typing import Iterable, Optional

import streamlit as st
import requests

st.set_page_config(page_title="Streamlit Chat Test Suit", page_icon="*", layout="wide")

# ---------- Config ---------- #
CHAT_STREAM_URL = os.getenv("CHAT_STREAM_URL", "")
AZURE_AD_TOKEN  = os.getenv("AZURE_AD_TOKEN", "")


st.title("Streamlit Chat Test Suit (Azure)")
mode = st.sidebar.radio("Mode", ["Chat only", "Chat with RAG", "Document Generation"])


# ---------- Helpers ----------
def auth_headers() -> dict:
    h = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    if AZURE_AD_TOKEN:
        h["Authorization"] = f"Bearer {AZURE_AD_TOKEN}"
    return h

def sse_lines(resp:requests.Response) -> Iterable[str]:
    """ Yields lines from a server sent event response."""
    for line in resp.iter_lines(decode_unicode=True, chunk_size=1):
        if not line:
            continue
        line = line.strip()
        if line.startswith("data:"):
            yield line[len("data:") :].strip()
        else:
            yield line

def token_from_json_line(line: str) -> Optional[str]:
    """Extract only 'answer' tokens from mixed SSE/event lines."""
    try:
        # Handle lines like: "event: message{...json...}" by stripping prefix before first '{'
        brace = line.find("{")
        if brace != -1:
            line = line[brace:]
        j = json.loads(line)
    except Exception:
        return None

    # Prefer structured payloads: {"event":"message","data":{"type":"answer","content":"..."}}
    data = j.get("data")
    if isinstance(data, dict):
        t = data.get("type")
        if t == "answer":
            v = data.get("content")
            return v if isinstance(v, str) else None
        # ignore other types like "thought", "talk"
        return None

    # Fallbacks for simpler schemas
    for k in ("content", "token", "text"):
        v = j.get(k)
        if isinstance(v, str):
            return v

    # OpenAI-style delta
    try:
        ch = j.get("choices", [])[0]
        delta = ch.get("delta", {})
        v = delta.get("content")
        if isinstance(v, str):
            return v
    except Exception:
        pass
    return None

# ---------- Session state ----------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "histories" not in st.session_state:
    # each = {"title", "messages":[{"role","content"}]}
    st.session_state.histories = []
if "history_index" not in st.session_state:
    st.session_state.history_index = None

def new_history(title: str):
    st.session_state.histories.append({"title": title, "messages": []})
    st.session_state.history_index = len(st.session_state.histories) - 1

def current_history():
    if st.session_state.history_index is None:
        return None
    return st.session_state.histories[st.session_state.history_index]

# ---------- UI: left histories / right chat ----------
left, right = st.columns([1, 2])

with left:
    st.subheader("Chat histories")
    titles = [h["title"] or f"Session {i+1}" for i, h in enumerate(st.session_state.histories)]
    if titles:
        idx = st.radio(
            "Select a session",
            options=list(range(len(titles))),
            format_func=lambda i: titles[i],
            index=(st.session_state.history_index or 0),
        )
        st.session_state.history_index = idx
    else:
        st.info("No histories yet. Create one below.")

    default_title = time.strftime("Session • %Y-%m-%d %H:%M")
    title = st.text_input("New session title", value=default_title)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("➕ New session"):
            new_history(title.strip() or default_title)
    with col_b:
        if st.button("🗑️ Delete selected") and st.session_state.history_index is not None:
            st.session_state.histories.pop(st.session_state.history_index)
            st.session_state.history_index = None

with right:
    st.subheader("Mode & chat")
    mode = st.radio(
        "Mode (sent as feedback to backend)",
        ["Chat only", "Chat with RAG", "Document gen"],
        horizontal=True,
    )
    mode_value = {"Chat only": "chat", "Chat with RAG": "rag", "Document gen": "doc"}[mode]

    st.caption("This app uses a single streaming endpoint and sends `control.mode` to help your service toggle retrieval/doc-gen.")

    # Ensure we have a session
    if st.session_state.history_index is None and not st.session_state.histories:
        new_history(default_title)
    sess = current_history()

    # Render past messages
    if sess:
        for m in sess["messages"]:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

    # Chat input
    user_msg = st.chat_input("Type your question or instruction…")
    if user_msg and sess:
        # add user message
        sess["messages"].append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)

        # stream assistant
        with st.chat_message("assistant"):
            # bounded box
            box = st.empty()
            acc = ""
            try:
                last_user_msg = next(
                    (m["content"] for m in reversed(sess["messages"]) if m.get("role") == "user"),
                    ""
                )
                payload = {
                    "user_id": "test-user",
                    "query": last_user_msg,
                    "session_id": None,  # or an existing session UUID
                }

                resp = requests.post(
                    CHAT_STREAM_URL,
                    json=payload,
                    headers=auth_headers(),
                    timeout=120,
                    stream=True,
                )
                resp.raise_for_status()

                for line in sse_lines(resp):
                    if line == "[DONE]":
                        break

                    # handle optional error/session/info frames if your API sends them
                    try:
                        j = json.loads(line[line.find("{"):])  # robustly parse JSON portion
                        if "error" in j:
                            st.error(j["error"])
                            continue
                    except Exception:
                        pass

                    tok = token_from_json_line(line)
                    if tok is None:
                        continue  # skip non-answer frames

                    acc += tok
                    box.markdown(
                        f"<div style='border:1px solid #bbb;border-radius:8px;padding:12px;min-height:60px'>{acc}</div>",
                        unsafe_allow_html=True
                    )


            except Exception as e:
                st.error(f"Stream failed: {e}")

            # persist final assistant message
            sess["messages"].append({"role": "assistant", "content": acc})

st.markdown("---")
st.caption("Single-endpoint mode: this UI sends `messages` + optional `session_id` + `control.mode` to your /api/v1/chat/stream.")
