"""
Test script para validar el hybrid OCR (pypdf → Vision API) con preprocesado.
"""

import sys
sys.path.insert(0, 'f:\\MecaEnergy')

from app.services.ocr import _preprocess_fragmented_text, _sanity_energy


def test_preprocess():
    """Test función de preprocesado para unir números fragmentados"""
    
    # Test 1: Fecha fragmentada
    text1 = "Fecha: 1\n7/09/2025"
    result1 = _preprocess_fragmented_text(text1)
    print(f"Test 1 - Fecha fragmentada:")
    print(f"  Input:  {repr(text1)}")
    print(f"  Output: {repr(result1)}")
    assert "17/09/2025" in result1
    print("  ✅ PASS\n")
    
    # Test 2: Consumo fragmentado
    text2 = "Consumo total: 8\n3,895 kWh"
    result2 = _preprocess_fragmented_text(text2)
    print(f"Test 2 - Consumo fragmentado:")
    print(f"  Input:  {repr(text2)}")
    print(f"  Output: {repr(result2)}")
    assert "83,895" in result2 or "83.895" in result2
    print("  ✅ PASS\n")
    
    # Test 3: Periodo fragmentado (múltiples)
    text3 = "del 1\n7/09/2025 a 1\n9/10/2025"
    result3 = _preprocess_fragmented_text(text3)
    print(f"Test 3 - Periodo doble fragmentado:")
    print(f"  Input:  {repr(text3)}")
    print(f"  Output: {repr(result3)}")
    assert "17/09/2025" in result3
    assert "19/10/2025" in result3
    print("  ✅ PASS\n")


def test_sanity_dias():
    """Test sanity check de días (mínimo 15 días)"""
    
    # Test 1: 8 días (rechazar)
    result1 = _sanity_energy({"dias_facturados": 8})
    print(f"Test 4 - Sanity 8 días (rechazar):")
    print(f"  Input:  dias_facturados=8")
    print(f"  Output: {result1.get('dias_facturados')}")
    assert result1.get('dias_facturados') is None
    print("  ✅ PASS (rechazado correctamente)\n")
    
    # Test 2: 28 días (aceptar)
    result2 = _sanity_energy({"dias_facturados": 28})
    print(f"Test 5 - Sanity 28 días (aceptar):")
    print(f"  Input:  dias_facturados=28")
    print(f"  Output: {result2.get('dias_facturados')}")
    assert result2.get('dias_facturados') == 28
    print("  ✅ PASS (aceptado)\n")
    
    # Test 3: 370 días (límite superior, aceptar)
    result3 = _sanity_energy({"dias_facturados": 370})
    print(f"Test 6 - Sanity 370 días (límite superior):")
    print(f"  Input:  dias_facturados=370")
    print(f"  Output: {result3.get('dias_facturados')}")
    assert result3.get('dias_facturados') == 370
    print("  ✅ PASS (aceptado)\n")


if __name__ == "__main__":
    print("=" * 60)
    print("TEST HYBRID OCR A+C")
    print("=" * 60)
    print()
    
    try:
        test_preprocess()
        print("=" * 60)
        test_sanity_dias()
        print("=" * 60)
        print("\n✅ TODOS LOS TESTS PASARON\n")
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
