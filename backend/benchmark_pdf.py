import sys, time
import pdfplumber

pdf_path = r'data\income_tax_act.pdf'
MAX_TEST_PAGES = 10
print(f'Testing extraction speed on first {MAX_TEST_PAGES} pages...')

t0 = time.time()
with pdfplumber.open(pdf_path) as pdf:
    total = len(pdf.pages)
    print(f'PDF opened in {time.time()-t0:.2f}s. Total pages: {total}')
    for i in range(min(MAX_TEST_PAGES, total)):
        tp = time.time()
        text = pdf.pages[i].extract_text(x_tolerance=2, y_tolerance=2) or ''
        print(f'  Page {i+1}: {len(text)} chars in {time.time()-tp:.2f}s')

elapsed = time.time()-t0
rate = MAX_TEST_PAGES/elapsed
print(f'Rate: {rate:.2f} pages/sec. Estimated for {total}: {total/rate/60:.1f} min')
