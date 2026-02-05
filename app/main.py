import sys
from pathlib import Path
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field
import pandas as pd
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.document_extractor import DocumentExtractor

# ------------------- Schemas -------------------
class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None

class Invoice(BaseModel):
    vendor_name: str = Field(..., description="Vendor / Seller name")
    invoice_number: str
    invoice_date: Optional[date] = None
    line_items: List[LineItem] = Field(default_factory=list)

class PackingList(BaseModel):
    po_number: str = Field(..., alias="order_number")
    ship_to_address: str
    line_items: List[LineItem] = Field(default_factory=list)

# ------------------- Classification -------------------
def classify_document(md_text: str) -> str:
    text = md_text.lower()
    if any(k in text for k in ["invoice", "bill to", "invoice no", "total due"]):
        return "invoice"
    if any(k in text for k in ["packing list", "pack list", "po number", "ship to"]):
        return "packing_list"
    return "unknown"  # fallback

# ------------------- Main processing -------------------
def process_document(file_path: Path):
    converter = DocumentConverter()
    result = converter.convert(file_path)
    doc = result.document
    md_text = doc.export_to_markdown()

    doc_type = classify_document(md_text)
    print(f"Classified as: {doc_type.upper()}")

    extractor = DocumentExtractor(allowed_formats=[InputFormat.PDF, InputFormat.IMAGE])

    if doc_type == "invoice":
        template = Invoice
        output_name = f"{file_path.stem}_invoice"
    elif doc_type == "packing_list":
        template = PackingList
        output_name = f"{file_path.stem}_packinglist"
    else:
        # fallback: try both and pick the one with fewer errors
        print("Ambiguous → trying Invoice schema first")
        template = Invoice
        output_name = f"{file_path.stem}_unknown"

    extraction = extractor.extract(source=file_path, template=template)
    data = extraction.pages[0].extracted_data  # usually first page has everything

    # Save
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # JSON
    with open(output_dir / f"{output_name}.json", "w") as f:
        f.write(pd.json_normalize([data]).to_json(orient="records", indent=2))

    # Excel
    df_header = pd.DataFrame([data]) if isinstance(data, dict) else pd.DataFrame(data)
    df_items = pd.DataFrame(data.get("line_items", []))
    with pd.ExcelWriter(output_dir / f"{output_name}.xlsx") as writer:
        df_header.to_excel(writer, sheet_name="Header", index=False)
        df_items.to_excel(writer, sheet_name="Line_Items", index=False)

    print(f"Saved → output/{output_name}.xlsx + .json")

# ------------------- Run on all samples -------------------
if __name__ == "__main__":
    samples_dir = Path("samples")
    for pdf in samples_dir.rglob("*.pdf"):
        process_document(pdf)
    for img in samples_dir.rglob("*.{jpg,jpeg,png}"):
        process_document(img)
