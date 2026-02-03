#!/usr/bin/env python3
"""
Test rápido de los cambios en OCR
Verifica que los consumos por período se extraen correctamente
"""

import sys
sys.path.insert(0, 'app')

from services.ocr import extract_data_from_pdf
import os

# Buscar PDFs en temp_facturas
facturas_dir = "temp_facturas"
pdf_files = [f for f in os.listdir(facturas_dir) if f.lower().endswith('.pdf')]

print("=" * 70)
print("TEST DE EXTRACCIÓN - CAMBIOS DE CONSUMOS POR PERÍODO")
print("=" * 70)

for pdf_file in sorted(pdf_files)[:2]:  # Probar primeras 2
    pdf_path = os.path.join(facturas_dir, pdf_file)
    print(f"\n[PDF] Procesando: {pdf_file}")
    print("-" * 70)
    
    try:
        with open(pdf_path, 'rb') as f:
            file_bytes = f.read()
        
        result = extract_data_from_pdf(file_bytes)
        
        print(f"OK CUPS: {result.get('cups')}")
        print(f"OK Cliente: {result.get('cliente')}")
        print(f"OK Total factura: {result.get('total_factura')}")
        print(f"OK Periodo dias: {result.get('dias_facturados')}")
        print(f"\nCONSUMOS:")
        print(f"   Consumo total: {result.get('consumo_kwh')} kWh")
        print(f"   P1 (Punta): {result.get('consumo_p1_kwh')} kWh")
        print(f"   P2 (Llano): {result.get('consumo_p2_kwh')} kWh")
        print(f"   P3 (Valle): {result.get('consumo_p3_kwh')} kWh")
        print(f"   P4: {result.get('consumo_p4_kwh')} kWh")
        print(f"   P5: {result.get('consumo_p5_kwh')} kWh")
        print(f"   P6: {result.get('consumo_p6_kwh')} kWh")
        
        print(f"\nPOTENCIAS:")
        print(f"   P1: {result.get('potencia_p1_kw')} kW")
        print(f"   P2: {result.get('potencia_p2_kw')} kW")
        
        print(f"\nOTROS:")
        print(f"   ATR: {result.get('atr')}")
        print(f"   IVA: {result.get('iva')}")
        print(f"   Alquiler: {result.get('alquiler_contador')}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("TEST COMPLETADO")
print("=" * 70)
