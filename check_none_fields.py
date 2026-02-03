#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from app.services.ocr import extract_data_from_pdf

# Naturgy
naturgy_bytes = open('temp_facturas/factura Naturgy.pdf', 'rb').read()
naturgy_result = extract_data_from_pdf(naturgy_bytes)
print(f"Naturgy dias_facturados: {naturgy_result.get('dias_facturados')}")

# HC Energia
hc_bytes = open('temp_facturas/Fra Agosto.pdf', 'rb').read()
hc_result = extract_data_from_pdf(hc_bytes)
print(f"HC Energia atr: {hc_result.get('atr')}")
