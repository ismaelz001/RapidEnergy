#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from app.services.ocr import extract_data_from_pdf
import json

result = extract_data_from_pdf(open('temp_facturas/Factura Iberdrola.pdf', 'rb').read())

print("\n" + "=" * 70)
print("DATOS EXTRAÍDOS - CAMPOS PARA CLIENTE")
print("=" * 70)

cliente_fields = {
    "nombre": result.get("titular"),
    "email": result.get("email"),
    "dni": result.get("dni"),
    "telefono": result.get("telefono"),
    "direccion": result.get("direccion"),
    "provincia": result.get("provincia"),
    "cups": result.get("cups"),
}

for field, value in cliente_fields.items():
    status = "✅" if value else "⚠️"
    print(f"{status} {field:15} = {value}")

print("\n" + "=" * 70)
