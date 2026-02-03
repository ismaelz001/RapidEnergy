#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from app.services.ocr import extract_data_from_pdf

pdf_bytes = open('temp_facturas/Factura.pdf', 'rb').read()
result = extract_data_from_pdf(pdf_bytes)

print(f"Cliente: {result.get('titular')}")
print(f"Direccion: {result.get('direccion')}")
print(f"Localidad: {result.get('localidad')}")
