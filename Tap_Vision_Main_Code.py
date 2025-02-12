import streamlit as st
import pytesseract
from PIL import Image
import pyttsx3
from docx import Document
import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from gtts import gTTS
import os
import socket
import speech_recognition as sr
from transformers import MarianMTModel, MarianTokenizer,pipeline


st.set_page_config(page_title="Text Extraction and Speech App", layout="wide")

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\HP\anaconda3\Lib\Tesseract-OCR\tesseract.exe"

# Load translation models and tokenizers
@st.cache_resource
def load_translation_models():
    translation_models = {
        "en": None,  # No translation needed for English
        "hi": MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-hi"),  # English to Hindi
        "fr": MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-fr"),  # English to French
        "de": MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-de"),  # English to German
    }
    translation_tokenizers = {
        "en": None,  # No tokenizer needed for English
        "hi": MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-hi"),
        "fr": MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-fr"),
        "de": MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-de"),
    }
    return translation_models, translation_tokenizers

translation_models, translation_tokenizers = load_translation_models()

# Function to translate text
def translate_text(text, target_lang):
    if target_lang == "en":
        return text  # No translation needed for English
    if target_lang not in translation_models:
        st.error(f"Translation to {target_lang} is not supported.")
        return text
    model = translation_models[target_lang]
    tokenizer = translation_tokenizers[target_lang]
    translated = tokenizer.encode(text, return_tensors="pt", truncation=True, max_length=512)
    translated_text = model.generate(translated, max_length=512)
    return tokenizer.decode(translated_text[0], skip_special_tokens=True)

@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

summarizer = load_summarizer()

# Function to summarize text
def summarize_text(text):
    if len(text.split()) > 50:
        summary = summarizer(text, max_length=100, min_length=30, do_sample=False)
        return summary[0]['summary_text']
    return text  # Return original text if too short


# Function to extract text from an image using OCR (Tesseract)
def read_image(file_obj):
    try:
        img = Image.open(file_obj)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        st.error(f"Error reading image: {e}")
        return ""

# Function to read PDF files
def read_pdf(file_obj):
    doc = fitz.open(stream=file_obj.read(), filetype="pdf")
    text = "".join(page.get_text() for page in doc)
    doc.close()
    return text

# Function to read Word documents
def read_word(file_obj):
    doc = Document(file_obj)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)

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
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

        if response.status_code == 403:
            st.error("\U0001f6a8 This website doesn't allow extracting data. Try another website.")
            return ""

        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text()
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())

    except requests.exceptions.RequestException as e:
        st.error(f" Error fetching URL: {e}")
        return ""

# Function to determine the format and read the content
def read_text(file_obj=None, file_type=None, url=None):
    if url:
        return read_web_page(url)
    elif file_type == 'pdf':
        return read_pdf(file_obj)
    elif file_type == 'docx':
        return read_word(file_obj)
    elif file_type == 'epub':
        return read_epub(file_obj)
    elif file_type == 'txt':
        return read_plain_text(file_obj)
    elif file_type in ['jpg', 'jpeg', 'png']:
        return read_image(file_obj)
    else:
        st.error(" Unsupported file format!")
        return ""

# Function to check internet availability
def is_internet_available():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

# Function to convert text to speech using gTTS (Online)
def text_to_speech_with_gtts(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang)
        output_audio_path = "output_audio.mp3"
        tts.save(output_audio_path)
        return output_audio_path
    except Exception as e:
        st.error(f"Error generating speech with gTTS: {e}")
        return None

# Function to convert text to speech using pyttsx3 (Offline)
def text_to_speech_with_pyttsx3(text):
    try:
        engine = pyttsx3.init()
        output_audio_path = "output_audio.mp3"
        engine.save_to_file(text, output_audio_path)
        engine.runAndWait()
        return output_audio_path
    except Exception:
        st.error(" Error generating speech with pyttsx3.")
        return None

# Function to choose TTS engine automatically
def text_to_speech_auto(text, lang="en"):
    if not text:
        st.error(" No text available for speech conversion.")
        return None
    # Use gTTS for non-English languages
    if lang != "en":
        return text_to_speech_with_gtts(text, lang)
    return text_to_speech_with_pyttsx3(text) if not is_internet_available() else text_to_speech_with_gtts(text, lang)

# Function to recognize speech and return the recognized text
def recognize_speech_from_mic(prompt="\U0001f3a4 Listening... Please speak now."):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info(prompt)

        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio)
            st.success(f"Recognized Command: {command}")
            return command.lower().strip()
        except sr.UnknownValueError:
            st.warning(" Couldn't recognize your voice. Please try again.")
        except sr.RequestError:
            st.error(" Voice recognition service is unavailable.")
        return None

# Streamlit UI


st.title("\U0001f4d6 TapVision (Combine 'Tap' interaction method with 'Vision' for accessibility)")

st.markdown("*Extract text from files, URLs, images, and convert to audio.*")

uploaded_file = st.file_uploader("\U0001f4c2 Upload a file (PDF, DOCX, EPUB, TXT, or Image)", type=["pdf", "docx", "epub", "txt", "jpg", "jpeg", "png"])

url_input = st.text_input("\U0001f310 Or enter a URL")

content = ""
if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()
    content = read_text(file_obj=uploaded_file, file_type=file_type)
    st.text_area("\U0001f4dc Extracted Text", content, height=300)

if url_input:
    content = read_text(url=url_input)
    st.text_area("\U0001f310 Extracted Text from URL", content, height=300)

# # content = read_text(file_obj=uploaded_file, file_type=uploaded_file.name.split(".")[-1] if uploaded_file else None, url=url_input)
# if content:
#     st.info("Would you like to summarize the text? Say 'yes' or 'no'.")
#     if recognize_speech_from_mic() == "yes":
#         content = summarize_text(content)
#     text_to_speech_auto(content)
    
# if content:
#     st.info("would you like to summarize the text? 'yes' or 'no'")
#     command= recognize_speech_from_mic()
#     if command and "yes" in command:
#         language_command = recognize_speech_from_mic("\U0001f3a4 Listening for yes or no...")
#         content = summarize_text(content)
#     text_to_speech_auto(content)
    
# if content:
#     st.info("Please say 'convert to speech' to start the audio conversion.")
#     command = recognize_speech_from_mic()

#     if command and "convert to speech" in command:
#         st.info("Please say the preferred language (e.g., English, Hindi, French, German).")
#         language_command = recognize_speech_from_mic("\U0001f3a4 Listening for language preference...")

#         language_mapping = {
#             "english": "en",
#             "hindi": "hi",
#             "french": "fr",
#             "german": "de"
#         }

#         selected_language = language_mapping.get(language_command.lower(), "en")

#         if selected_language == "en" and language_command.lower() not in language_mapping:
#             st.warning(f"Language '{language_command}' not recognized. Defaulting to English.")

#         # Translate the content to the selected language
#         with st.spinner("Translating text..."):
#             translated_text = translate_text(content, selected_language)
#             st.text_area("\U0001f4dc Translated Text", translated_text, height=300)

#         # Convert the translated text to speech
#         audio_file_path = text_to_speech_auto(translated_text, lang=selected_language)
#         if audio_file_path and os.path.exists(audio_file_path):
#             st.audio(audio_file_path, format="audio/mp3", start_time=0)

# if content:
#     st.info("Would you like to summarize the text? Say 'yes' or 'no'.")
#     command = recognize_speech_from_mic("\U0001f3a4 yes or no")
#     if command and "yes" in command.lower():
#         content = summarize_text(content)

    
#     st.info("Say 'convert to speech' to start audio conversion.")
#     command = recognize_speech_from_mic()
    
#     if command and "convert to speech" in command:
#         st.info("Say the preferred language (e.g., English, Hindi, French, German).")
#         language_command = recognize_speech_from_mic("\U0001f3a4 Listening for language preference...")

#         language_mapping = {
#             "english": "en",
#             "hindi": "hi",
#             "french": "fr",
#             "german": "de"
#         }

#         selected_language = language_mapping.get(language_command.lower(), "en")

#         if selected_language == "en" and language_command.lower() not in language_mapping:
#             st.warning(f"Language '{language_command}' not recognized. Defaulting to English.")

#         translated_text = translate_text(content, selected_language)
#         st.text_area("\U0001f4dc Translated Text", translated_text, height=300)
        
#         audio_file_path = text_to_speech_auto(translated_text, lang=selected_language)
#         if audio_file_path and os.path.exists(audio_file_path):
#             st.audio(audio_file_path, format="audio/mp3", start_time=0)

# if content:
#     st.info("say summarize to  summarize the text")
#     command = recognize_speech_from_mic()
    
#     if command:
#         st.info(f"You said: {command}")
#         if any(word in command.lower() for word in ["summarize","sumarize","summarise","sumarise"]):
#             content = summarize_text(content)
#         elif any(word in command.lower() for word in ["no", "nope", "nah"]):
#             st.info("Summarization skipped.")
#     else:
#         st.warning("Speech recognition failed. Please try again.")

#     st.info("Say 'convert to speech' to start audio conversion.")
#     command = recognize_speech_from_mic()
    
#     if command and "convert to speech" in command.lower():
#         st.info("Say the preferred language (e.g., English, Hindi, French, German).")
#         language_command = recognize_speech_from_mic("\U0001f3a4 Listening for language preference...")

#         language_mapping = {
#             "english": "en",
#             "hindi": "hi",
#             "french": "fr",
#             "german": "de"
#         }

#         selected_language = language_mapping.get(language_command.lower(), "en")

#         if selected_language == "en" and language_command.lower() not in language_mapping:
#             st.warning(f"Language '{language_command}' not recognized. Defaulting to English.")

#         translated_text = translate_text(content, selected_language)
#         st.text_area("\U0001f4dc Translated Text", translated_text, height=300)
        
#         audio_file_path = text_to_speech_auto(translated_text, lang=selected_language)
#         if audio_file_path and os.path.exists(audio_file_path):
#             st.audio(audio_file_path, format="audio/mp3", start_time=0)

if content:
    # Ask the user if they want to summarize the text
    st.info("Say 'summarize' to summarize the text.")
    command = recognize_speech_from_mic()
    
    if command:
        st.info(f"You said: {command}")
        # Check if the user said something similar to "summarize"
        if any(word in command.lower() for word in ["summarize", "sumarize", "summarise", "sumarise"]):
            # Summarize the content
            summarized_content = summarize_text(content)
            st.info("Text summarized successfully!")
            # Display the summarized content
            st.text_area("Summarized Text", summarized_content, height=300)
            # Update the content variable to use the summarized text for subsequent steps
            content = summarized_content
        elif any(word in command.lower() for word in ["no", "nope", "nah"]):
            st.info("Summarization skipped.")
        else:
            st.warning("Command not recognized. Please say 'summarize' or 'no'.")
    else:
        st.warning("Speech recognition failed. Please try again.")

    # Ask the user if they want to convert the text to speech
    st.info("Say 'convert to speech' to start audio conversion.")
    command = recognize_speech_from_mic()
    
    if command and "convert to speech" in command.lower():
        st.info("Say the preferred language (e.g., English, Hindi, French, German).")
        language_command = recognize_speech_from_mic("\U0001f3a4 Listening for language preference...")

        language_mapping = {
            "english": "en",
            "hindi": "hi",
            "french": "fr",
            "german": "de"
        }

        selected_language = language_mapping.get(language_command.lower(), "en")

        if selected_language == "en" and language_command.lower() not in language_mapping:
            st.warning(f"Language '{language_command}' not recognized. Defaulting to English.")

        # Translate the content (original or summarized) to the selected language
        translated_text = translate_text(content, selected_language)
        st.text_area("\U0001f4dc Translated Text", translated_text, height=300)
        
        # Convert the translated text to speech
        audio_file_path = text_to_speech_auto(translated_text, lang=selected_language)
        if audio_file_path and os.path.exists(audio_file_path):
            st.audio(audio_file_path, format="audio/mp3", start_time=0)