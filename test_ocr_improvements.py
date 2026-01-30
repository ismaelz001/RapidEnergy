#!/usr/bin/env python3
"""
Test script for OCR improvements (Facturas 288, 289, 291)
Validates fecha extraction improvements and consumo extraction strategies
"""
import sys
import re
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / "app"))
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ocr import _extract_table_consumos, normalize_text, _parse_date_flexible, parse_es_number

# Test cases based on QA audit findings
TEST_CASES = {
    "factura_288_periodo_dates": {
        "description": "Factura 288 - Missing periodo dates, should have fecha_inicio/fin",
        "text": """
FACTURA Nº 288
CONSUMIDOR
PERIODO DE CONSUMO: 5 de junio al 9 de agosto de 2024

Lectura anterior:    12.345 kWh
Lectura actual:      12.649 kWh
CONSUMO TOTAL:       304 kWh
        """,
        "expected": {
            "fecha_inicio_consumo": "5 de junio",
            "fecha_fin_consumo": "9 de agosto",
            "should_contain_year": True,
        }
    },
    
    "factura_288_del_format": {
        "description": "Factura 288 - Alternative format: 'del DD de MES al DD de MES de YYYY'",
        "text": """
FACTURA Nº 288
Del 5 de junio al 9 de agosto de 2024
P1: 59 kWh
P2: 0 kWh  
P3: 245 kWh
        """,
        "expected": {
            "fecha_inicio_consumo": "5 de junio de 2024",
            "fecha_fin_consumo": "9 de agosto de 2024",
        }
    },
    
    "factura_289_partial_consumos": {
        "description": "Factura 289 - P1/P2/P3 values with zeros, only P3 was being extracted",
        "text": """
CONSUMOS DESAGREGADOS
P1 (PUNTA):       0 kWh
P2 (LLANO):       0 kWh
P3 (VALLE):     304 kWh
TOTAL:          304 kWh
        """,
        "expected": {
            "consumo_p1_kwh": 0,
            "consumo_p2_kwh": 0,
            "consumo_p3_kwh": 304,
        }
    },
    
    "factura_289_section_header": {
        "description": "Factura 289 - Table with section header 'CONSUMOS DESAGREGADOS'",
        "text": """
CONSUMOS DESAGREGADOS
PERIODO | PUNTA | LLANO | VALLE | TOTAL
Aug     |   0   |   0   |  304  | 304
        """,
        "expected": {
            "should_parse": True,
            "consumo_p3_kwh": 304,
        }
    },
    
    "factura_291_all_zeros": {
        "description": "Factura 291 - Complete consumo extraction failure (all zeros)",
        "text": """
FACTURA Nº 291
PERIODO DE CONSUMO: 10 de septiembre al 8 de octubre de 2024

Detalles de consumo:
P1: 45
P2: 23
P3: 156
Consumo total: 224 kWh
        """,
        "expected": {
            "consumo_p1_kwh": 45,
            "consumo_p2_kwh": 23,
            "consumo_p3_kwh": 156,
        }
    },
}


def test_date_extraction():
    """Test new fecha extraction formats"""
    print("\n" + "="*70)
    print("TEST: Fecha Extraction Improvements")
    print("="*70)
    
    from app.services.ocr import parse_invoice_text
    
    for test_name, test_case in TEST_CASES.items():
        if "periodo_dates" not in test_name and "del_format" not in test_name:
            continue
            
        print(f"\n[TEST] {test_case['description']}")
        print("-" * 70)
        
        result = parse_invoice_text(test_case["text"])
        
        fecha_inicio = result.get("fecha_inicio_consumo")
        fecha_fin = result.get("fecha_fin_consumo")
        
        print(f"  fecha_inicio_consumo: {fecha_inicio}")
        print(f"  fecha_fin_consumo:    {fecha_fin}")
        
        # Check if extracted correctly
        expected = test_case["expected"]
        if "fecha_inicio_consumo" in expected:
            if fecha_inicio and expected["fecha_inicio_consumo"] in fecha_inicio:
                print("  ✅ PASS: fecha_inicio extracted correctly")
            else:
                print(f"  ❌ FAIL: Expected '{expected['fecha_inicio_consumo']}', got '{fecha_inicio}'")
        
        if "fecha_fin_consumo" in expected:
            if fecha_fin and expected["fecha_fin_consumo"] in fecha_fin:
                print("  ✅ PASS: fecha_fin extracted correctly")
            else:
                print(f"  ❌ FAIL: Expected '{expected['fecha_fin_consumo']}', got '{fecha_fin}'")


def test_consumo_extraction():
    """Test _extract_table_consumos() function"""
    print("\n" + "="*70)
    print("TEST: Consumo Table Extraction (_extract_table_consumos)")
    print("="*70)
    
    for test_name, test_case in TEST_CASES.items():
        if "consumo" not in test_name and "all_zeros" not in test_name:
            continue
        
        print(f"\n[TEST] {test_case['description']}")
        print("-" * 70)
        
        # Test _extract_table_consumos directly
        result = _extract_table_consumos(test_case["text"])
        
        for i in range(1, 4):
            key = f"consumo_p{i}_kwh"
            val = result.get(key)
            print(f"  {key}: {val}")
        
        # Verify expected values
        expected = test_case["expected"]
        all_pass = True
        for key, expected_val in expected.items():
            if key == "should_parse":
                continue
            if key in result:
                actual_val = result[key]
                if actual_val == expected_val:
                    print(f"  ✅ PASS: {key} = {expected_val}")
                else:
                    print(f"  ❌ FAIL: {key} expected {expected_val}, got {actual_val}")
                    all_pass = False
            else:
                print(f"  ❌ FAIL: {key} not found in result")
                all_pass = False


def test_integration():
    """Test full parse_invoice_text integration"""
    print("\n" + "="*70)
    print("TEST: Integration (Full parse_invoice_text)")
    print("="*70)
    
    from app.services.ocr import parse_invoice_text
    
    test_case = TEST_CASES["factura_291_all_zeros"]
    print(f"\n[TEST] {test_case['description']}")
    print("-" * 70)
    
    result = parse_invoice_text(test_case["text"])
    
    # Print all consumo fields
    for i in range(1, 7):
        key = f"consumo_p{i}_kwh"
        val = result.get(key)
        print(f"  {key}: {val}")
    
    # Check expected values
    expected = test_case["expected"]
    all_pass = True
    for key, expected_val in expected.items():
        actual_val = result.get(key)
        if actual_val == expected_val:
            print(f"  ✅ PASS: {key} = {expected_val}")
        else:
            print(f"  ❌ FAIL: {key} expected {expected_val}, got {actual_val}")
            all_pass = False


if __name__ == "__main__":
    print("\n" + "🧪 OCR IMPROVEMENTS TEST SUITE 🧪".center(70))
    print("Testing fecha and consumo extraction enhancements")
    
    try:
        test_date_extraction()
        test_consumo_extraction()
        test_integration()
        
        print("\n" + "="*70)
        print("TEST SUMMARY: All critical paths tested ✅")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
