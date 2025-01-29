import tempfile
import os
from llama_index.readers.file.docs import PDFReader, DocxReader

def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from a PDF file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name
    try:
        reader = PDFReader()
        documents = reader.load_data(temp_path)
        text = "\n".join(doc.text for doc in documents)
        return text
    finally:
        os.unlink(temp_path)

def extract_text_from_docx(content: bytes) -> str:
    """Extract text from a DOCX file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name
    try:
        reader = DocxReader()
        documents = reader.load_data(temp_path)
        text = "\n".join(doc.text for doc in documents)
        return text
    finally:
        os.unlink(temp_path) 