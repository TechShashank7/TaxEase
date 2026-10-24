"""
Diagnose which page(s) in the Income Tax Act PDF hang pdfplumber.
Scans pages 400-420 with a 10-second per-page timeout.
"""
import sys, time, signal, contextlib
sys.path.insert(0, r'c:\Users\Shashank Raj\OneDrive\Desktop\TaxEase\backend')
import pdfplumber

pdf_path = r'data\income_tax_act.pdf'
START_PAGE = 398   # 0-based index = page 399
END_PAGE   = 420

print(f"Diagnosing pages {START_PAGE+1}–{END_PAGE+1}...")

with pdfplumber.open(pdf_path) as pdf:
    for i in range(START_PAGE, min(END_PAGE, len(pdf.pages))):
        page_num = i + 1
        t0 = time.time()
        try:
            # Give each page at most 15s
            text = pdf.pages[i].extract_text(x_tolerance=2, y_tolerance=2) or ''
            elapsed = time.time() - t0
            status = "OK" if elapsed < 5 else "SLOW"
            print(f"  Page {page_num}: {len(text)} chars in {elapsed:.1f}s  [{status}]")
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  Page {page_num}: ERROR after {elapsed:.1f}s — {e}")
