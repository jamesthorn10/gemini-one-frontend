import streamlit as st
import requests
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Career Mentor",
    page_icon="🤖",
    layout="centered"
)

# --- Backend API Configuration ---
# This is the public URL of your working backend on Hugging Face.
BACKEND_URL = "https://jatingoyal10-gemini-two.hf.space"

# --- Session State Management ---
# This is how Streamlit remembers things between user interactions.
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_uploaded" not in st.session_state:
    st.session_state.resume_uploaded = False
if "filename" not in st.session_state:
    st.session_state.filename = None

# --- API Functions ---
def upload_resume(uploaded_file):
    """Sends the resume to the backend API."""
    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/pdf')}
    try:
        response = requests.post(f"{BACKEND_URL}/upload-resume", files=files, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"API connection failed: {e}"}

def query_backend(prompt):
    """Sends a question to the backend API."""
    try:
        response = requests.post(f"{BACKEND_URL}/query", json={"prompt": prompt}, timeout=180)
        response.raise_for_status()
        result = response.json()
        
        # Simple cleanup to remove the echoed prompt from the response
        bot_message = result.get("response", "Sorry, an empty response was received.")
        answer_marker = "Your Answer:"
        answer_position = bot_message.rfind(answer_marker)
        if answer_position != -1:
            bot_message = bot_message[answer_position + len(answer_marker):].strip()
        
        return bot_message

    except requests.exceptions.RequestException as e:
        return f"Error: The request to the AI backend failed. {e}"

def reset_backend():
    """Tells the backend to clear its memory of the resume."""
    try:
        requests.post(f"{BACKEND_URL}/reset")
    except requests.exceptions.RequestException:
        pass # It's fine if this fails, we just reset the UI anyway

# --- UI Rendering ---

st.title("🤖 AI Career Mentor")
st.markdown("Get personalized career advice by chatting with an AI coach about your resume.")

# Sidebar for file upload and controls
with st.sidebar:
    st.header("Your Resume")
    
    # Disable the uploader if a resume is already loaded
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF)", 
        type="pdf", 
        disabled=st.session_state.resume_uploaded
    )

    if uploaded_file is not None and not st.session_state.resume_uploaded:
        with st.spinner("Analyzing your resume..."):
            result = upload_resume(uploaded_file)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.resume_uploaded = True
                st.session_state.filename = result.get("filename")
                # Add the initial greeting from the assistant
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"I've finished analyzing **{st.session_state.filename}**. What would you like to know?"
                })
                st.rerun() # Rerun the script to update the main page

    if st.session_state.resume_uploaded:
        st.success(f"Loaded: {st.session_state.filename}")
        st.info("You can now ask questions in the chat window.")

    if st.button("Start Over with New Resume"):
        reset_backend()
        # Reset all session state variables
        st.session_state.messages = []
        st.session_state.resume_uploaded = False
        st.session_state.filename = None
        st.rerun()

# Main chat interface
st.header("Chat with your Mentor")

# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle new user input
if prompt := st.chat_input("What are my strongest skills based on my resume?"):
    if not st.session_state.resume_uploaded:
        st.warning("Please upload your resume in the sidebar first.")
    else:
        # Add user message to state and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get and display the assistant's response
        with st.chat_message("assistant"):
            with st.spinner("The AI is thinking..."):
                response = query_backend(prompt)
                st.markdown(response)
        
        # Add assistant message to state
        st.session_state.messages.append({"role": "assistant", "content": response})
