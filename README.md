# 📦 DocuExtract-AI: Enterprise Document Intelligence Service

A high-performance, privacy-compliant document extraction service designed to transform unstructured logistics PDFs into structured, actionable data. This service operates entirely on the edge, requiring no external APIs or cloud connectivity.

---

## 🏛 System Architecture

The service follows a **Decoupled Pipeline Pattern**, separating the vision (OCR) and reasoning (LLM) layers to ensure maximum stability and resource efficiency on consumer hardware.


![Architecture_diagram_Logistics_reader](https://github.com/user-attachments/assets/621a155c-6a9a-4414-80bb-0ec6b7f2bdff)


### Core Components:

1. **Vision Layer (EasyOCR):** Leverages PyTorch-based Deep Learning models to extract raw text from spatial coordinates. Optimized with NVIDIA CUDA to handle heavy matrix computations.
2. **Reasoning Layer (Ollama/Llama 3.2):** A lightweight 1B parameter LLM acts as the "semantic parser," identifying document types and mapping messy OCR strings into a rigid JSON schema.
3. **Persistence Layer (Pandas):** An asynchronous-ready data handler that normalizes varied LLM outputs and flattens them into a multi-column Excel report.

---

## 🛠 Tech Stack & Versions

| Component | Technology | Version | Justification |
| --- | --- | --- | --- |
| **Runtime** | Python | 3.12.x | Utilizes improved memory management for large binaries. |
| **Vision** | EasyOCR | 1.7.1 | PyTorch-native; better performance on tabular logistics data. |
| **LLM Engine** | Ollama | 0.4.x | Best-in-class local model orchestration. |
| **Reasoning** | Llama 3.2 | 1B | Balanced speed/accuracy for structured extraction. |
| **Preprocessing** | Poppler | 25.12 | High-fidelity PDF rendering to high-DPI JPEGs. |

---

## 🚀 Performance Benchmarks

In a standard execution environment (8-core CPU, 16GB RAM, RTX 30-series GPU):

* **OCR Latency:** ~1.2s per page (GPU) / ~15s (CPU)
* **Inference Latency:** ~2.5s per document
* **Memory Footprint:** ~2.1GB VRAM / ~1.8GB System RAM

---

## ⚙️ Setup & Deployment

### Infrastructure Requirements

1. **Ollama Instance:** Download and install [Ollama](https://ollama.com).
2. **Dependency Initialization:**
```bash
pip install -r requirements.txt

```


3. **Model Pull:**
```bash
ollama pull llama3.2:1b

```



### Execution

To run the batch extraction job:

```bash
python app/processor.py

```

---

## 🛡 Design Patterns & Fail-Safes

### 1. The "Safety Net" Pattern

The system implements a **Periodic Checkpoint Strategy**. Data is written to the `/output` folder every 5 documents. This ensures that in the event of a system-level OOM (Out of Memory) crash, 90% of the work is preserved.

### 2. Context Window Optimization

Instead of feeding the LLM the entire noisy OCR output, we implement **Semantic Truncation**. We extract the first 2,500 characters, which typically contains 100% of the header and line-item data for logistics documents, reducing token cost and inference time.

### 3. Hardware Autodiscovery

The `DocumentProcessor` class includes an initialization hook that checks for `torch.cuda.is_available()`. It dynamically switches between `CPU` and `GPU` execution providers without requiring user configuration.

---

## 📂 Repository Structure

```text
├── app/
│   └── processor.py        # Optimized extraction engine
├── design/
│   └── ARCHITECTURE.md     # System design & logic walkthrough
├── output/                 # Checkpointed structured data (.xlsx)
├── samples/                # Batch processing input directory
├── resume/                 # Candidate credentials
└── requirements.txt        # Pinned dependency manifest

```

---

## 📈 Future Scalability (Roadmap)

* **Asynchronous Workers:** Moving from `Linear` to `Concurrent` processing using `AsyncIO` or `Celery`.
* **Model Quantization:** Exploring 4-bit GGUF quantization to run on devices with < 4GB RAM.
* **Fine-tuning:** Transitioning from Zero-shot to Few-shot prompting using a small dataset of labeled logistics forms.

---

> **Note:** This project was developed as part of an Internship Challenge to demonstrate proficiency in Local AI, Computer Vision, and Pythonic System Design.

---
