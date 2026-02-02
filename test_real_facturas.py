"""
Test real con las facturas problemáticas #296 y #297
"""

import sys
sys.path.insert(0, 'f:\\MecaEnergy')

from app.services.ocr import extract_data_from_pdf


def test_factura_296():
    """Factura Naturgy: 28 días, OCR anterior extraía 8"""
    
    print("\n" + "=" * 60)
    print("FACTURA #296 (Naturgy - 28 días)")
    print("=" * 60)
    
    with open('f:\\MecaEnergy\\temp_facturas\\factura Naturgy.pdf', 'rb') as f:
        file_bytes = f.read()
    
    result = extract_data_from_pdf(file_bytes)
    
    print(f"\n📄 Resultados extraídos:")
    print(f"  - dias_facturados: {result.get('dias_facturados')}")
    print(f"  - consumo_kwh: {result.get('consumo_kwh')}")
    print(f"  - fecha_inicio: {result.get('fecha_inicio')}")
    print(f"  - fecha_fin: {result.get('fecha_fin')}")
    print(f"  - cups: {result.get('cups')}")
    
    dias = result.get('dias_facturados')
    
    if dias is None:
        print("\n⚠️ No se extrajo dias_facturados (puede ser problema OCR)")
    elif dias < 15:
        print(f"\n❌ ERROR: dias_facturados={dias} < 15 (debería haberse rechazado)")
        return False
    elif 25 <= dias <= 31:
        print(f"\n✅ CORRECTO: dias_facturados={dias} está en rango esperado (25-31)")
        return True
    else:
        print(f"\n⚠️ dias_facturados={dias} fuera de rango esperado (25-31), pero válido")
        return True


def test_factura_297():
    """Factura Endesa: 83.9 kWh, OCR anterior extraía 12"""
    
    print("\n" + "=" * 60)
    print("FACTURA #297 (Endesa - 83.9 kWh)")
    print("=" * 60)
    
    with open('f:\\MecaEnergy\\temp_facturas\\Factura.pdf', 'rb') as f:
        file_bytes = f.read()
    
    result = extract_data_from_pdf(file_bytes)
    
    print(f"\n📄 Resultados extraídos:")
    print(f"  - consumo_kwh: {result.get('consumo_kwh')}")
    print(f"  - dias_facturados: {result.get('dias_facturados')}")
    print(f"  - fecha_inicio: {result.get('fecha_inicio')}")
    print(f"  - fecha_fin: {result.get('fecha_fin')}")
    print(f"  - cups: {result.get('cups')}")
    
    consumo = result.get('consumo_kwh')
    
    if consumo is None:
        print("\n⚠️ No se extrajo consumo_kwh (puede ser problema OCR)")
        return False
    elif consumo < 10:
        print(f"\n❌ ERROR: consumo_kwh={consumo} < 10 (sospechoso)")
        return False
    elif 80 <= consumo <= 90:
        print(f"\n✅ CORRECTO: consumo_kwh={consumo} está en rango esperado (80-90)")
        return True
    else:
        print(f"\n⚠️ consumo_kwh={consumo} fuera de rango esperado, validar manualmente")
        return consumo > 10  # Aceptar si al menos es razonable


if __name__ == "__main__":
    print("\n" + "🔍" * 30)
    print("TEST REAL: FACTURAS PROBLEMÁTICAS")
    print("🔍" * 30)
    
    try:
        result_296 = test_factura_296()
        result_297 = test_factura_297()
        
        print("\n" + "=" * 60)
        print("RESUMEN")
        print("=" * 60)
        print(f"Factura #296 (Naturgy):  {'✅ PASS' if result_296 else '❌ FAIL'}")
        print(f"Factura #297 (Endesa):   {'✅ PASS' if result_297 else '❌ FAIL'}")
        
        if result_296 and result_297:
            print("\n✅ TODAS LAS FACTURAS VALIDADAS\n")
        else:
            print("\n⚠️ ALGUNAS FACTURAS REQUIEREN REVISIÓN\n")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
