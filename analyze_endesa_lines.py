#!/usr/bin/env python3
from pypdf import PdfReader

pdf_bytes = open('temp_facturas/Factura.pdf', 'rb').read()
reader = PdfReader(open('temp_facturas/Factura.pdf', 'rb'))
full_text = reader.pages[0].extract_text()

raw_lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]

# Buscar ANTONIO + siguientes líneas
for i, line in enumerate(raw_lines):
    if "ANTONIO RUIZ" in line:
        print(f"[{i}] {line}")
        for j in range(1, 6):
            if i+j < len(raw_lines):
                print(f"[{i+j}] {raw_lines[i+j]}")
        break

print("\n=== Líneas con DIRECCION/ESTACION ===")
for i, line in enumerate(raw_lines):
    if "DIRECCI" in line.upper() or "ESTACION" in line.upper():
        print(f"[{i}] {line}")
