#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from app.services.ocr import extract_data_from_pdf

pdf_bytes = open('temp_facturas/Fra Agosto.pdf', 'rb').read()
result = extract_data_from_pdf(pdf_bytes)

print(f"Cliente: {result.get('titular')}")
print(f"Fecha inicio: {result.get('fecha_inicio_consumo')}")
print(f"Fecha fin: {result.get('fecha_fin_consumo')}")
print(f"Dias: {result.get('dias_facturados')}")
print(f"Consumo kWh: {result.get('consumo_kwh')}")
