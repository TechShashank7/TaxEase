import sys
import json
sys.path.insert(0, r'c:\Users\Shashank Raj\OneDrive\Desktop\TaxEase\backend')
import pdfplumber
from app.services.rag.pdf_ingestion import _clean_page_text
from app.services.rag.chunker import chunk_document

pdf_path = r'c:\Users\Shashank Raj\OneDrive\Desktop\TaxEase\backend\data\income_tax_act.pdf'

pages_data = []
# Just grab the first 3 pages of the document to demonstrate chunking and metadata extraction
with pdfplumber.open(pdf_path) as pdf:
    for i in range(3):
        raw = pdf.pages[i].extract_text(x_tolerance=2, y_tolerance=2) or ''
        cleaned = _clean_page_text(raw)
        if cleaned.strip():
            pages_data.append((i+1, cleaned))

chunks = chunk_document(pages_data, source_document='income_tax_act.pdf', max_tokens=400, overlap_tokens=50)

with open(r'c:\Users\Shashank Raj\OneDrive\Desktop\TaxEase\backend\data\sample_chunks.json', 'w', encoding='utf-8') as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)
