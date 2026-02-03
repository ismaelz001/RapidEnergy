#!/usr/bin/env python3
"""
Test limpio de validacion de los cambios OCR (sin emojis para PowerShell)
"""
import json
import sys
from pathlib import Path

# Agregar path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ocr import extract_data_from_pdf

# Cargar ground truth
try:
    with open("temp_facturas/ground_truth.json", "r", encoding="utf-8") as f:
        ground_truth = json.load(f)
except:
    print("[ERROR] No se puede cargar ground_truth.json")
    sys.exit(1)

# Test files (key must match ground_truth.json)
test_files = {
    "Iberdrola": "temp_facturas/Factura Iberdrola.pdf",
    "Naturgy": "temp_facturas/factura Naturgy.pdf", 
    "Endesa": "temp_facturas/Factura.pdf",
    "HC_Energia": "temp_facturas/Fra Agosto.pdf"
}

print("=" * 80)
print("VALIDACION DE CAMBIOS OCR")
print("=" * 80)

total_tests = 0
passed_tests = 0
failed_tests = 0

for company, pdf_path in test_files.items():
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"\n[SKIP] {company}: archivo no existe ({pdf_path})")
        continue
    
    print(f"\n{'=' * 80}")
    print(f"COMPANY: {company.upper()}")
    print(f"FILE: {pdf_path}")
    print(f"{'=' * 80}")
    
    # Extract
    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        result = extract_data_from_pdf(pdf_bytes)
        gt = ground_truth[company]
    except Exception as e:
        print(f"[ERROR] Extraccion fallo: {e}")
        continue
    
    # Test 1: Cliente (baseline)
    total_tests += 1
    gt_cliente = gt.get("titular") or gt.get("cliente")
    if result.get("cliente") == gt_cliente:
        print(f"[PASS] Cliente: {result.get('cliente')}")
        passed_tests += 1
    else:
        print(f"[FAIL] Cliente: OCR='{result.get('cliente')}' vs GT='{gt_cliente}'")
        failed_tests += 1
    
    # Test 2: Dias facturados (FIX #1 - rango expandido)
    if gt.get("dias_facturados"):
        total_tests += 1
        ocr_dias = result.get("dias_facturados")
        gt_dias = gt["dias_facturados"]
        if ocr_dias == gt_dias:
            print(f"[PASS] Dias facturados: {ocr_dias} dias (FIX #1 OK)")
            passed_tests += 1
        else:
            diff = ocr_dias - gt_dias if ocr_dias and ocr_dias else 'N/A'
            print(f"[FAIL] Dias facturados: OCR={ocr_dias} vs GT={gt_dias} (diff: {diff})")
            failed_tests += 1
    
    # Test 3: Consumos por periodo (FIX #3 - Strategy 0)
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
                details.append(f"P1: {ocr_p1:.2f} OK")
            else:
                details.append(f"P1: OCR={ocr_p1} vs GT={gt_p1} FAIL")
                match = False
        
        if gt_p2 is not None:
            if ocr_p2 and abs(ocr_p2 - gt_p2) < 1.0:
                details.append(f"P2: {ocr_p2:.2f} OK")
            else:
                details.append(f"P2: OCR={ocr_p2} vs GT={gt_p2} FAIL")
                match = False
        
        if gt_p3 is not None:
            if ocr_p3 and abs(ocr_p3 - gt_p3) < 1.0:
                details.append(f"P3: {ocr_p3:.2f} OK")
            else:
                details.append(f"P3: OCR={ocr_p3} vs GT={gt_p3} FAIL")
                match = False
        
        if match:
            print(f"[PASS] Consumos periodo (FIX #3 OK): {', '.join(details)}")
            passed_tests += 1
        else:
            print(f"[FAIL] Consumos periodo (FIX #3): {', '.join(details)}")
            failed_tests += 1
    
    # Test 4: Consumo total (validacion basica)
    total_tests += 1
    gt_total = gt.get("consumo_kwh")
    ocr_total = result.get("consumo_kwh")
    
    if gt_total and ocr_total and abs(ocr_total - gt_total) < 1.0:
        print(f"[PASS] Consumo total: {ocr_total:.2f} kWh")
        passed_tests += 1
    else:
        print(f"[FAIL] Consumo total: OCR={ocr_total} vs GT={gt_total}")
        failed_tests += 1
    
    # Test 5: Potencias
    if gt.get("potencia_p2_kw"):
        total_tests += 1
        ocr_pot = result.get("potencia_p2_kw")
        gt_pot = gt["potencia_p2_kw"]
        
        if ocr_pot and abs(ocr_pot - gt_pot) < 0.5:
            print(f"[PASS] Potencia P2: {ocr_pot:.1f} kW")
            passed_tests += 1
        else:
            print(f"[FAIL] Potencia P2: OCR={ocr_pot} vs GT={gt_pot}")
            failed_tests += 1

print(f"\n{'=' * 80}")
print(f"RESUMEN")
print(f"{'=' * 80}")
print(f"Total tests: {total_tests}")
print(f"Passed: {passed_tests}")
print(f"Failed: {failed_tests}")
print(f"Rate: {100 * passed_tests / total_tests:.1f}% OK" if total_tests > 0 else "No tests run")
