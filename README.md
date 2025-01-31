Text-to-Speech Application

This is a Streamlit-based Text-to-Speech (TTS) application that extracts text from various file formats, web pages, and converts it into speech using pyttsx3.

Features

Supports file uploads: PDF, DOCX, EPUB, and TXT.

Extracts and reads text from web pages.

Converts extracted text to speech using pyttsx3.

Allows customization of:

Voice gender (Male/Female)

Speech speed (Adjustable)

Volume control

Generates an MP3 audio file for download.

Installation

Prerequisites

Ensure you have Python installed (>=3.7) and install the required dependencies.

pip install streamlit pyttsx3 python-docx pymupdf requests beautifulsoup4 ebooklib

Running the Application

Run the following command in your terminal:

streamlit run app.py

Usage

Upload a file (PDF, DOCX, EPUB, or TXT) or enter a URL.

The extracted text will be displayed in a text area.

Choose voice settings (Male/Female, Speed, Volume).

Click "Convert to Speech" to generate an MP3 file.

Play or download the generated speech audio.

Technologies Used

Python (Primary programming language)

Streamlit (UI framework)

pyttsx3 (Text-to-Speech conversion)

PyMuPDF (Fitz) (PDF extraction)

python-docx (Word document parsing)

ebooklib (EPUB file handling)

BeautifulSoup & Requests (Web scraping)

Author

Aditya Kumar

License

This project is licensed under the MIT License.

