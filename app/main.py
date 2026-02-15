import json
import logging
from pathlib import Path
import pandas as pd
from processor import DocumentProcessor

# Configure logging for cleaner output
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Project Paths using pathlib (cleaner than os.path)
BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = BASE_DIR / 'samples'
OUTPUT_DIR = BASE_DIR / 'output'

def save_to_excel(data: dict, output_path: Path):
    """
    Exports the extracted data to an Excel file with separate sheets
    for the document summary and the line items.
    """
    if not data:
        logger.warning("No data available to save.")
        return

    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: Metadata / Summary
            metadata = data.get('metadata', {})
            summary_df = pd.DataFrame([metadata])
            
            # Insert document type at the start for visibility
            summary_df.insert(0, 'Document Type', data.get('document_type', 'Unknown'))
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Sheet 2: Line Items
            items = data.get('line_items', [])
            items_df = pd.DataFrame(items) if items else pd.DataFrame()
            items_df.to_excel(writer, sheet_name='Line Items', index=False)
            
        logger.info(f"Saved Excel report: {output_path.name}")
        
    except Exception as e:
        logger.error(f"Failed to save Excel file {output_path.name}: {e}")

def process_single_file(file_path: Path, processor: DocumentProcessor):
    """
    Handles the OCR and AI extraction pipeline for a single file.
    """
    logger.info(f"Processing: {file_path.name}")

    # 1. Extract text via OCR
    try:
        raw_text = processor.extract_text(str(file_path))
        if not raw_text:
            logger.warning(f"OCR returned no text for {file_path.name}. Skipping.")
            return
    except Exception as e:
        logger.error(f"OCR error on {file_path.name}: {e}")
        return

    # 2. Process text with the LLM
    try:
        result_json = processor.process_document(raw_text)
    except Exception as e:
        logger.error(f"AI processing error on {file_path.name}: {e}")
        return

    # 3. Save outputs if successful
    if result_json:
        # Define output paths
        base_name = file_path.stem
        json_output = OUTPUT_DIR / f"{base_name}.json"
        excel_output = OUTPUT_DIR / f"{base_name}.xlsx"

        # Save JSON
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, indent=4)
        
        # Save Excel
        save_to_excel(result_json, excel_output)

def main():
    """Main execution entry point."""
    logger.info("Starting Document Extraction Service")

    # validation
    if not SAMPLES_DIR.exists() or not any(SAMPLES_DIR.iterdir()):
        logger.warning(f"No files found in {SAMPLES_DIR}. Please add images to process.")
        return

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize the processor
    # Using llama3.2:1b as it's lightweight and good for JSON structure
    model_name = "llama3.2:1b"
    try:
        processor = DocumentProcessor(model_name=model_name)
    except Exception as e:
        logger.critical(f"Could not initialize Ollama ({model_name}). Check if the service is running. Error: {e}")
        return

    # Filter for valid image/document types
    valid_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.pdf'}
    
    count = 0
    for file_path in SAMPLES_DIR.iterdir():
        # Skip hidden files or unsupported types
        if file_path.name.startswith('.') or file_path.suffix.lower() not in valid_extensions:
            continue
        
        process_single_file(file_path, processor)
        count += 1

    logger.info(f"Job complete. Processed {count} files.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
