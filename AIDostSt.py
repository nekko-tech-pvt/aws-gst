import streamlit as st
import requests
import json
import time
import numpy as np
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from PyPDF2 import PdfReader

# Azure Document Intelligence Credentials
ENDPOINT = "https://gstdosvision.cognitiveservices.azure.com/"
KEY = "5k0wVN4IwWyGGSXFk3DL2CgympxmezmiIRr2T34z77vlWESc5TMGJQQJ99BAACYeBjFXJ3w3AAALACOGYecI"
document_analysis_client = DocumentAnalysisClient(ENDPOINT, credential=AzureKeyCredential(KEY))

# Azure OpenAI Credentials
LLM_API_URL = "https://kanan-m49gpffn-swedencentral.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"
LLM_API_KEY = "df9D3simI5RalfedvfQBPnuUg1PLTZcQuTStmUpu8BQ0EynYFAaLJQQJ99ALACfhMk5XJ3w3AAAAACOG4lEB"

# Function to extract text from PDF using Azure Document Intelligence
def extract_text_from_pdf(uploaded_file):
    poller = document_analysis_client.begin_analyze_document(
        "prebuilt-read", document=uploaded_file
    )
    result = poller.result()
    extracted_text = "\n".join([line.content for page in result.pages for line in page.lines])
    return extracted_text


# Function to call LLM API
def call_llm_api(system_message, user_query):
    headers = {"Content-Type": "application/json", "api-key": LLM_API_KEY}
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_query}
    ]
    payload = {"messages": messages, "temperature": 0.7, "max_tokens": 1048}
    response = requests.post(LLM_API_URL, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# Streamlit UI
st.set_page_config(page_title="NexusDMS", layout="wide")
if st.sidebar.button("New Chat"):
    st.session_state.conversation = []
    st.session_state.pdf_text = ""
    if "uploaded_file" in st.session_state:
        del st.session_state["uploaded_file"]

    st.sidebar.empty() 

st.sidebar.header("Upload Your Document📄")
uploaded_file = st.sidebar.file_uploader("Upload Document", type=["pdf", "jpg", "jpeg", "png"])

if "conversation" not in st.session_state:
    st.session_state.conversation = []
    st.session_state.pdf_text = ""

if uploaded_file:
    st.session_state.pdf_text = extract_text_from_pdf(uploaded_file)
    st.sidebar.success("PDF uploaded and processed successfully!")

st.image("AIDost.jpg", width=80)
st.title("AI DOST Document📄")
st.write("Upload PDF and ask questions about its content.")

user_query = st.chat_input("Ask a question about the document.")

if user_query and st.session_state.pdf_text:
    system_message = """
    You are a Helpful Legal Data Analyst specializing in legal document analysis. Your task is to do the following:
    
    - Your Primary Focus should Always be on how to protect and save the prime accused.
    - Focus on delivering answers that are directly related to the Question, ensuring that the response is as specific and actionable as possible based on the context you retrieve.
    - If the answer is not present in the context or if the query is ambiguous or vague, state that the information cannot be determined or is not available from the document.
    - Always provide any additional insights from the fetched contexts that may be relevant to the question, such as anomalies, contradictions, or key points that could aid in an investigation or analysis.
    - Note: Sometimes Contents of the same entity such as Tables can span over multiple consecutive pages. Your task is to identify the pages in order and consolidate them accordingly from the provided contexts.
    - The contexts you receive are outputs from OCR so expect them to have mistakes. Rely on your Intelligence to make corrections to the text as appropriate when formulating and presenting answers.
    - IMPORTANT: The Law is a Precise Endeavour. Never make up information you do not find in the contexts or provide your opinion on things unless explicitly asked.
    - Never use Double Quotes in your Answer. Use Backticks to highlight if necessary.
""" + st.session_state.pdf_text
    response = call_llm_api(system_message, user_query)
    
    st.session_state.conversation.append({"user": user_query, "assistant": response})

# Display previous conversation
for chat in st.session_state.conversation:
    with st.chat_message("user"):
        st.write(chat["user"])
    with st.chat_message("assistant"):
        st.write(chat["assistant"])
