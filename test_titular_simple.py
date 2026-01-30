#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from app.services.ocr import extract_data_from_pdf

result = extract_data_from_pdf(open('temp_facturas/Factura Iberdrola.pdf', 'rb').read())
print(f'Titular: {result.get("titular")}')
print(f'DNI: {result.get("dni")}')
