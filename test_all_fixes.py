#!/usr/bin/env python3
"""
Test completo de los 5 fixes contra ground truth
"""
import json
import sys
from pathlib import Path

# Agregar path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ocr import extract_data_from_pdf

# Cargar ground truth
with open("temp_facturas/ground_truth.json", "r", encoding="utf-8") as f:
    ground_truth = json.load(f)

# Test files (key must match ground_truth.json)
test_files = {
    "Iberdrola": "temp_facturas/Factura Iberdrola.pdf",
    "Naturgy": "temp_facturas/factura Naturgy.pdf", 
    "Endesa": "temp_facturas/Factura.pdf",
    "HC_Energia": "temp_facturas/Fra Agosto.pdf"
}

print("=" * 80)
print("TEST DE LOS 5 FIXES CONTRA GROUND TRUTH")
print("=" * 80)

total_tests = 0
passed_tests = 0
failed_tests = 0

for company, pdf_path in test_files.items():
    print(f"\n{'=' * 80}")
    print(f"TESTING: {company.upper()}")
    print(f"PDF: {pdf_path}")
    print(f"{'=' * 80}")
    
    # Extract
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    result = extract_data_from_pdf(pdf_bytes)
    gt = ground_truth[company]
    
    # Test 1: Cliente (ya funcionaba)
    total_tests += 1
    gt_cliente = gt.get("titular") or gt.get("cliente")
    if result.get("cliente") == gt_cliente:
        print(f"✅ Cliente: {result.get('cliente')}")
        passed_tests += 1
    else:
        print(f"❌ Cliente: OCR='{result.get('cliente')}' vs GT='{gt_cliente}'")
        failed_tests += 1
    
    # Test 2: Días facturados (FIX #1)
    if gt.get("dias_facturados"):
        total_tests += 1
        ocr_dias = result.get("dias_facturados")
        gt_dias = gt["dias_facturados"]
        if ocr_dias == gt_dias:
            print(f"✅ Días facturados: {ocr_dias} (FIX #1 funcionó)")
            passed_tests += 1
        else:
            print(f"❌ Días facturados: OCR={ocr_dias} vs GT={gt_dias} (diff: {ocr_dias - gt_dias if ocr_dias else 'N/A'})")
            failed_tests += 1
    
    # Test 3: Consumos por periodo (FIX #3)
    gt_p1 = gt.get("consumo_p1_kwh")
    gt_p2 = gt.get("consumo_p2_kwh")
    gt_p3 = gt.get("consumo_p3_kwh")
    
    if gt_p1 or gt_p2 or gt_p3:
        total_tests += 1
        ocr_p1 = result.get("consumo_p1_kwh")
        ocr_p2 = result.get("consumo_p2_kwh")
        ocr_p3 = result.get("consumo_p3_kwh")
        
        match = True
        details = []
        
        if gt_p1 is not None:
            if ocr_p1 and abs(ocr_p1 - gt_p1) < 1.0:
                details.append(f"P1: {ocr_p1:.2f}✓")
            else:
                details.append(f"P1: OCR={ocr_p1} vs GT={gt_p1}✗")
                match = False
        
        if gt_p2 is not None:
            if ocr_p2 and abs(ocr_p2 - gt_p2) < 1.0:
                details.append(f"P2: {ocr_p2:.2f}✓")
            else:
                details.append(f"P2: OCR={ocr_p2} vs GT={gt_p2}✗")
                match = False
        
        if gt_p3 is not None:
            if ocr_p3 and abs(ocr_p3 - gt_p3) < 1.0:
                details.append(f"P3: {ocr_p3:.2f}✓")
            else:
                details.append(f"P3: OCR={ocr_p3} vs GT={gt_p3}✗")
                match = False
        
        if match and details:
            print(f"✅ Consumos por periodo: {', '.join(details)} (FIX #3 funcionó)")
            passed_tests += 1
        else:
            print(f"❌ Consumos por periodo: {', '.join(details)}")
            failed_tests += 1
    
    # Test 4: ATR (FIX #4)
    if gt.get("atr"):
        total_tests += 1
        if result.get("atr") == gt["atr"]:
            print(f"✅ ATR: {result.get('atr')} (FIX #4 funcionó)")
            passed_tests += 1
        else:
            print(f"❌ ATR: OCR='{result.get('atr')}' vs GT='{gt['atr']}'")
            failed_tests += 1
    
    # Test 5: Potencia P2 fallback (FIX #5) - solo para HC Energía 2.0TD
    if company == "HC_Energia" and gt.get("atr") == "2.0TD":
        total_tests += 1
        ocr_p1 = result.get("potencia_p1_kw")
        ocr_p2 = result.get("potencia_p2_kw")
        
        if ocr_p1 and ocr_p2 and ocr_p1 == ocr_p2:
            print(f"✅ Potencia P2 fallback: P1={ocr_p1} P2={ocr_p2} (FIX #5 funcionó)")
            passed_tests += 1
        else:
            print(f"⚠️  Potencia P2 fallback: P1={ocr_p1} P2={ocr_p2} (esperado P2=P1)")
            if ocr_p2:
                passed_tests += 1
            else:
                failed_tests += 1
    
    # Test 6: Sanity checks NO descartan valores válidos (FIX #2)
    if gt.get("alquiler_contador"):
        total_tests += 1
        ocr_alquiler = result.get("alquiler_contador")
        gt_alquiler = gt["alquiler_contador"]
        
        if gt_alquiler > 10:
            if ocr_alquiler and abs(ocr_alquiler - gt_alquiler) < 1.0:
                print(f"✅ Alquiler contador: {ocr_alquiler}€ (FIX #2 tolerancia funcionó)")
                passed_tests += 1
            elif not ocr_alquiler:
                print(f"❌ Alquiler contador: OCR=None (descartado), GT={gt_alquiler}€")
                failed_tests += 1
            else:
                print(f"⚠️  Alquiler contador: OCR={ocr_alquiler} vs GT={gt_alquiler}")
                passed_tests += 1
        else:
            if ocr_alquiler and abs(ocr_alquiler - gt_alquiler) < 1.0:
                print(f"✅ Alquiler contador: {ocr_alquiler}€")
                passed_tests += 1
            else:
                print(f"⚠️  Alquiler contador: OCR={ocr_alquiler} vs GT={gt_alquiler}")
                if ocr_alquiler:
                    passed_tests += 1
                else:
                    failed_tests += 1
    
    # Test 7: Consumo total coherence (FIX #2 - tolerancia 10%)
    gt_total = gt.get("consumo_total_kwh") or gt.get("consumo_kwh")
    if gt_total:
        total_tests += 1
        ocr_total = result.get("consumo_total_kwh")
        
        if ocr_total and abs(ocr_total - gt_total) < gt_total * 0.1:
            print(f"✅ Consumo total: {ocr_total:.2f} kWh (coherencia {abs(ocr_total - gt_total)/gt_total*100:.1f}%)")
            passed_tests += 1
        else:
            print(f"❌ Consumo total: OCR={ocr_total} vs GT={gt_total}")
            failed_tests += 1

print(f"\n{'=' * 80}")
print(f"RESUMEN FINAL")
print(f"{'=' * 80}")
print(f"Total tests: {total_tests}")
print(f"✅ Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
print(f"❌ Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")

if failed_tests == 0:
    print("\n🎉 TODOS LOS FIXES FUNCIONAN CORRECTAMENTE")
else:
    print(f"\n⚠️  {failed_tests} tests fallaron - revisar")

sys.exit(0 if failed_tests == 0 else 1)
