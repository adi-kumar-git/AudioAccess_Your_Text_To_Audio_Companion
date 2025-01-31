import streamlit as st
import pyttsx3
from docx import Document
import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from io import BytesIO
import os

# Function to read PDF files
def read_pdf(file_obj):
    doc = fitz.open(stream=file_obj.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

# Function to read Word documents
def read_word(file_obj):
    doc = Document(file_obj)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

# Function to read ePub files
def read_epub(file_obj):
    book = epub.read_epub(file_obj)
    text = ""
    for item in book.get_items():
        if item.get_type() == epub.EpubHtml:
            soup = BeautifulSoup(item.content, 'html.parser')
            text += soup.get_text() + "\n"
    return text

# Function to read plain text files
def read_plain_text(file_obj):
    return file_obj.read().decode("utf-8")

# Function to fetch and extract text from web pages
def read_web_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())

# Main function to determine the format and read the content
def read_text(file_obj, file_type=None, is_url=False):
    if is_url:
        return read_web_page(file_obj)
    elif file_type == 'pdf':
        return read_pdf(file_obj)
    elif file_type == 'docx':
        return read_word(file_obj)
    elif file_type == 'epub':
        return read_epub(file_obj)
    elif file_type == 'txt':
        return read_plain_text(file_obj)
    else:
        st.error("Unsupported file format!")
        return ""

# Function to convert text to speech with pyttsx3
def text_to_speech_with_pyttsx3(text, voice_gender="male", speed=150, volume=1.0):
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        selected_voice = None
        for voice in voices:
            if voice_gender.lower() in voice.name.lower():
                selected_voice = voice
                break
        if not selected_voice:
            selected_voice = voices[0]

        engine.setProperty('voice', selected_voice.id)
        engine.setProperty('rate', speed)
        engine.setProperty('volume', volume)
        output_audio_path = "output_audio.mp3"
        engine.save_to_file(text, output_audio_path)
        engine.runAndWait()
        st.success("Audio saved as output_audio.mp3")
        return output_audio_path
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# Streamlit UI
st.set_page_config(page_title="Text-to-Speech App", layout="wide")

st.title("Text-to-Speech Application")
st.markdown("Extract text from files, URLs, and convert to audio.")

uploaded_file = st.file_uploader("Upload a file (PDF, DOCX, EPUB, TXT)", type=["pdf", "docx", "epub", "txt"])
url_input = st.text_input("Or enter a URL")

content = ""
if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()
    content = read_text(uploaded_file, file_type)
    st.text_area("Extracted Text", content, height=300)

if url_input:
    content = read_text(url_input, is_url=True)
    st.text_area("Extracted Text from URL", content, height=300)

if content:
    voice_gender = st.radio("Choose voice", ("male", "female"))
    speed = st.slider("Select speech speed", min_value=100, max_value=200, value=150)
    volume = st.slider("Select volume", min_value=0.0, max_value=1.0, value=1.0)

    if st.button("Convert to Speech"):
        audio_file_path = text_to_speech_with_pyttsx3(content, voice_gender, speed, volume)
        if audio_file_path and os.path.exists(audio_file_path):
            st.audio(audio_file_path, format="audio/mp3")


