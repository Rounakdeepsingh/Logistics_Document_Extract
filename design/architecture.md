Document Extraction Service - Design Document
1. Tech Stack
Language: Python 3.12

OCR Engine: EasyOCR (Local, GPU-accelerated) - Chosen for its offline capabilities and high accuracy on table structures without API costs.

LLM Engine: Ollama running llama3.2:1b - Chosen for its low memory footprint (vram optimized) and ability to run locally on consumer hardware.

Orchestration: LangChain - Used to interface with the local LLM.

Data Handling: Pandas & OpenPyXL - For structured data manipulation and Excel export.

2. Component Architecture
Flow: PDF Input -> Image Conversion -> EasyOCR (Vision) -> Raw Text -> Llama 3.2 (Reasoning) -> JSON -> Excel Output

Diagram:

Preprocessor: Uses pdf2image to convert documents into high-res images.

Vision Layer: EasyOCR scans the image. We utilize NVIDIA CUDA acceleration for parallel processing (10x speedup).

Context Window Optimization: We extract only the first 2500 characters of text to prevent LLM hallucination and memory overflow.

Extraction Layer: Llama 3.2:1b receives a structured prompt to classify the document (Invoice vs. Packing List) and extract specific JSON fields.

Persistence Layer: Data is aggregated and saved to .xlsx every 5 files to ensure data safety during batch processing.

3. Logic & Exception Handling
Blurred/Empty Images: The system checks if raw_text length is < 10 characters. If so, it logs a warning and skips the file to prevent crashing.

Hallucinations: We use a strict JSON schema in the prompt. If the LLM returns invalid JSON, the system catches the json.JSONDecodeError and flags the file as "Error" in the output rather than crashing the pipeline.

Memory Management: The system explicitly detects CUDA availability. If a GPU is present, it offloads OCR tasks to VRAM. If not, it falls back to CPU.

4. Limitations
Column Sparsity: Due to the generative nature of LLMs, key names (e.g., "Invoice No" vs "Invoice #") may vary slightly, creating sparse columns in the final Excel sheet. A normalization layer would be added in production.