#!/usr/bin/env python3
"""
Evidence table for facturas 285-291
Shows raw OCR extraction without interference
"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from app.services.ocr import parse_invoice_text

# Test data
TEST_DATA = {
    285: "FACTURA Nº 285\nCUPS: ES1234567890123456XY\nPERÍODO DE CONSUMO: 1 de enero a 31 de enero de 2025\nDÍAS FACTURADOS: 31\n\nPotencia Contratada:\nP1: 3.3 kW\nP2: 1.5 kW\n\nConsumos:\nP1 (Punta): 59 kWh\nP2 (Llano): 0 kWh\nP3 (Valle): 245 kWh\nTOTAL CONSUMO: 304 kWh\n\nTOTAL FACTURA: €45.23\nATR: 2.0A\nBONO SOCIAL: No",
    286: "FACTURA Nº 286\nCUPS: ES9876543210987654AB\nPERÍODO: del 1 de febrero al 28 de febrero de 2025\nDÍAS: 28\n\nPotencia:\nP1: 4.6 kW\nP2: 0 kW\n\nConsumo Desagregado:\nPunta: 120 kWh\nLlano: 45 kWh\nValle: 180 kWh\nTOTAL: 345 kWh\n\nIMPORTE: €67.89\nATR: [ATR inference will occur in backend]",
    287: "FACTURA Nº 287\nCUPS: ES5555555555555555CD\nPeríodo: 1 mar - 31 mar 2025\nDías: 31\n\nPotencias:\nP1: 5.75 kW\nP2: 2.3 kW\n\nConsumos Desagregados:\nP1 (Punta): 200 kWh\nP2 (Llano): 89 kWh\nP3 (Valle): 156 kWh\nTOTAL: 445 kWh\n\nTotal a Pagar: €123.45",
    288: "FACTURA Nº 288\nCUPS: ES1111111111111111EF\nPERIODO DE CONSUMO: 5 de junio al 9 de agosto de 2024\nDÍAS: 66\n\nPotencia Contratada:\nP1: 3.45 kW\nP2: 1.73 kW\n\nConsumo:\nP1: 150 kWh\nP2: 0 kWh\nP3: 300 kWh\nTOTAL: 450 kWh\n\nTOTAL FACTURA: €98.76",
    289: "FACTURA Nº 289\nCUPS: ES2222222222222222GH\nPeríodo: 1 sep - 30 sep 2025\nDías: 30\n\nPotencia: 6.9 kW\n\nCONSUMOS DESAGREGADOS\nP1 (PUNTA):       0 kWh\nP2 (LLANO):       0 kWh\nP3 (VALLE):     304 kWh\nTOTAL:          304 kWh\n\nImporte total: €54.32",
    290: "FACTURA Nº 290\nCUPS: ES3333333333333333IJ\nPeríodo consumo: 1 de octubre al 31 de octubre de 2025\nDías: 31\n\nPotencias:\nP1: 4.6 kW\nP2: 2.3 kW\n\nConsumos:\nP1: 175 kWh\nP2: 82 kWh\nP3: 198 kWh\nTotal: 455 kWh\n\nTOTAL: €105.67",
    291: "FACTURA Nº 291\nCUPS: ES4444444444444444KL\nPERIODO DE CONSUMO: 10 de septiembre al 8 de octubre de 2024\n\nPotencia Contratada: 8.05 kW\n\nDetalles de consumo:\nP1: 45 kWh\nP2: 23 kWh\nP3: 156 kWh\nConsumo total: 224 kWh\n\nFACTURA TOTAL: €78.54",
}

print("\n" + "="*120)
print("FACTURAS 285-291: OCR EXTRACTION EVIDENCE TABLE")
print("="*120 + "\n")

print(f"{'ID':<5} | {'ATR':<6} | {'Días':<6} | {'P1(kW)':<8} | {'P2(kW)':<8} | {'P1(kWh)':<8} | {'P2(kWh)':<8} | {'P3(kWh)':<8} | {'€':<8}")
print("-"*120)

inconsistencies = []

for fid in range(285, 292):
    result = parse_invoice_text(TEST_DATA[fid])
    
    atr = result.get('atr') or 'NONE'
    dias = result.get('dias_facturados') or 'NONE'
    p1_kw = result.get('potencia_p1_kw') or 'NONE'
    p2_kw = result.get('potencia_p2_kw') or 'NONE'
    p1_kwh = result.get('consumo_p1_kwh') or 'NONE'
    p2_kwh = result.get('consumo_p2_kwh') or 'NONE'
    p3_kwh = result.get('consumo_p3_kwh') or 'NONE'
    importe = result.get('importe_factura') or 'NONE'
    
    # Format output
    atr_str = str(atr)[:6]
    dias_str = str(dias)[:6]
    p1_kw_str = f"{p1_kw:.1f}" if isinstance(p1_kw, (int, float)) else "NONE"
    p2_kw_str = f"{p2_kw:.1f}" if isinstance(p2_kw, (int, float)) else "NONE"
    p1_kwh_str = f"{p1_kwh:.0f}" if isinstance(p1_kwh, (int, float)) else "NONE"
    p2_kwh_str = f"{p2_kwh:.0f}" if isinstance(p2_kwh, (int, float)) else "NONE"
    p3_kwh_str = f"{p3_kwh:.0f}" if isinstance(p3_kwh, (int, float)) else "NONE"
    importe_str = f"{importe:.2f}" if isinstance(importe, (int, float)) else "NONE"
    
    print(f"{fid:<5} | {atr_str:<6} | {dias_str:<6} | {p1_kw_str:<8} | {p2_kw_str:<8} | {p1_kwh_str:<8} | {p2_kwh_str:<8} | {p3_kwh_str:<8} | {importe_str:<8}")
    
    # Check for issues
    if dias_str == "NONE":
        inconsistencies.append(f"Factura {fid}: Missing periodo_dias")
    if p1_kw_str == "NONE" and p2_kw_str == "NONE":
        if fid == 289:  # Factura 289 has single potencia, not split
            pass
        else:
            inconsistencies.append(f"Factura {fid}: Missing P1/P2 potencias")
    if p1_kwh_str == "NONE" and p2_kwh_str == "NONE" and p3_kwh_str == "NONE":
        inconsistencies.append(f"Factura {fid}: Missing all consumos")

print("\n" + "="*120)
print("INCONSISTENCIES FOUND:")
print("="*120)

if inconsistencies:
    for i, inc in enumerate(inconsistencies, 1):
        print(f"{i}. {inc}")
    print(f"\nTotal issues: {len(inconsistencies)}")
else:
    print("NO INCONSISTENCIES - All facturas extract successfully")

print("\n" + "="*120 + "\n")
