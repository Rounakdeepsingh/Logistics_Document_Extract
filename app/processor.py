import os
import logging
import json
import pandas as pd
import torch
from pdf2image import convert_from_path
import easyocr
from langchain_ollama import OllamaLLM

# --- CONFIGURATION ---
POPPLER_PATH = r"C:\poppler\poppler-25.12.0\Library\bin"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, model_name="llama3.2:1b"):
        # Check for GPU
        self.use_cuda = torch.cuda.is_available()
        device_name = "GPU (CUDA)" if self.use_cuda else "CPU"
        
        logger.info(f"--- INITIALIZING ON {device_name} ---")
        
        # Load OCR with GPU support if available
        self.reader = easyocr.Reader(['en'], gpu=self.use_cuda, verbose=False)
        
        # Connect to Ollama
        self.llm = OllamaLLM(model=model_name, temperature=0, num_ctx=2048)
        logger.info("--- SYSTEM READY ---")

    def extract_text_from_pdf(self, pdf_path):
        try:
            images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
            full_text = ""
            # Only processing the first page for the main data
            for i, image in enumerate(images[:1]):
                temp_img = f"temp_{i}.jpg"
                image.save(temp_img, "JPEG")
                result = self.reader.readtext(temp_img, detail=0)
                full_text += " ".join(result) + " "
                if os.path.exists(temp_img): os.remove(temp_img)
            return full_text
        except Exception as e:
            logger.error(f"OCR Error: {e}")
            return None

    def analyze_with_llm(self, ocr_text, filename):
        short_text = ocr_text[:2500]
        prompt = f"Convert this invoice text to JSON. Extract: Type, Vendor, Number, Date, Total, and Items. Text: {short_text}"
        try:
            logger.info(f"AI Analyzing: {filename}")
            response = self.llm.invoke(prompt)
            start = response.find('{')
            end = response.rfind('}') + 1
            return json.loads(response[start:end])
        except Exception as e:
            return {"filename": filename, "error": str(e)}

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    processor = DocumentProcessor()
    results = []

    pdf_files = []
    for root, _, files in os.walk(SAMPLES_DIR):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, f))

    logger.info(f"Processing {len(pdf_files)} files...")

    for i, path in enumerate(pdf_files):
        name = os.path.basename(path)
        text = processor.extract_text_from_pdf(path)
        if text:
            data = processor.analyze_with_llm(text, name)
            results.append(data)
        
        # Save every 5 files
        if (i + 1) % 5 == 0:
            pd.DataFrame(results).to_excel(os.path.join(OUTPUT_DIR, "extraction_results.xlsx"), index=False)

    pd.DataFrame(results).to_excel(os.path.join(OUTPUT_DIR, "extraction_results.xlsx"), index=False)
    logger.info("✅ ALL TASKS FINISHED!.")