#!/usr/bin/env python
from PyPDF2 import PdfReader

pdf_path = 'temp_facturas/Fra Agosto.pdf'
reader = PdfReader(pdf_path)
print(f'📄 PDF: {pdf_path}')
print(f'Páginas: {len(reader.pages)}')
print(f'\n=== CONTENIDO ===')
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    print(f'\n--- Página {i+1} ---')
    if text:
        print(text[:1500])
    else:
        print('Sin texto extraible')
