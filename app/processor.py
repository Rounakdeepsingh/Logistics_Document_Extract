import pytesseract
from langchain_core.messages import AIMessage
from pdf2image import convert_from_path
from PIL import Image
import json
import os
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

# --- CONFIGURATION ---
# This points to where you just installed Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class DocumentProcessor:
    def __init__(self, model_name="llama3.2:1b"):
        # This handles the connection to your local AI
        self.llm = ChatOllama(model=model_name, format="json")

    def extract_text(self, file_path):
        """Convert PDF or Image to raw text string using OCR."""
        text_content = ""
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.pdf':
                try:
                    images = convert_from_path(file_path)
                    for img in images:
                        text_content += pytesseract.image_to_string(img) + "\n"
                except Exception as e:
                    print(f" PDF Error: {e}")
                    return None
            elif ext in ['.png', '.jpg', '.jpeg']:
                text_content = pytesseract.image_to_string(Image.open(file_path))
            else:
                print(f" Unsupported file type: {ext}")
                return None
        except Exception as e:
            print(f" Error during OCR: {e}")
            return None
        return text_content

    def process_document(self, raw_text):
        """Send text to Local LLM for Classification and Extraction."""
        prompt = f"""
        You are a document extraction assistant. Analyze the following text.

        1. CLASSIFY: Is it an "Invoice" or "Packing List"?
        2. EXTRACT:
        - If Invoice: Vendor Name, Invoice Number, Date, Line Items.
        - If Packing List: Order Number, Ship-to Address, Line Items.
        Return ONLY valid JSON with this structure:
        {{
            "document_type": "Invoice",
            "metadata": {{
                "vendor_name": "...",
                "invoice_number": "...",
                "invoice_date": "...",
                "order_number": "...",
                "ship_to_address": "..."
            }},
            "line_items": [
                {{"description": "...", "quantity": "...", "unit_price": "...", "total": "..."}}
            ]
        }}

        DOCUMENT TEXT:
        {raw_text}
        """

        messages = [
            SystemMessage(content="You are a precise data extraction AI that outputs only JSON."),
            HumanMessage(content=prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            return json.loads(response.content)
        except Exception as e:
            print(f" AI Error: {e}")
            return None
