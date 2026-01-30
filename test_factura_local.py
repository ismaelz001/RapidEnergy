#!/usr/bin/env python3
"""
Test OCR local: Carga la factura Iberdrola y muestra qué extrae
"""

import sys
sys.path.insert(0, '/f:/MecaEnergy')

from app.services.ocr import extract_data_from_pdf
import json

factura_path = "f:/MecaEnergy/temp_facturas/Factura Iberdrola.pdf"

print("=" * 70)
print(f"LEYENDO FACTURA: {factura_path}")
print("=" * 70)

try:
    with open(factura_path, 'rb') as f:
        file_bytes = f.read()
    
    print(f"✅ Archivo leído: {len(file_bytes)} bytes\n")
    
    # Ejecutar OCR
    print("🔄 Extrayendo datos con OCR...\n")
    result = extract_data_from_pdf(file_bytes)
    
    print("=" * 70)
    print("RESULTADO DE EXTRACCIÓN:")
    print("=" * 70)
    
    # Pretty print del resultado
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 70)
    print("ANÁLISIS RÁPIDO:")
    print("=" * 70)
    
    checks = {
        "cups": "✅" if result.get("cups") else "❌",
        "atr": "✅" if result.get("atr") else "❌",
        "total_factura": "✅" if result.get("total_factura") else "❌",
        "consumo_kwh": "✅" if result.get("consumo_kwh") else "❌",
        "potencia_p1_kw": "✅" if result.get("potencia_p1_kw") else "❌",
        "potencia_p2_kw": "✅" if result.get("potencia_p2_kw") else "❌",
        "iva_porcentaje": "✅" if result.get("iva_porcentaje") else "❌",
    }
    
    for field, status in checks.items():
        value = result.get(field)
        print(f"{status} {field:20} = {value}")
    
except FileNotFoundError:
    print(f"❌ Archivo no encontrado: {factura_path}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
