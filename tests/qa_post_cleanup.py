"""
🧪 QA TEST POST-CLEANUP - Verificación Operativa Completa
"""
import os
import sys
import json
import requests
from pathlib import Path

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_test(name, status, details=""):
    """Print test result with color"""
    icon = "✅" if status else "❌"
    color = Colors.GREEN if status else Colors.RED
    print(f"{icon} {color}{name}{Colors.END}")
    if details:
        print(f"   {details}")

def test_imports():
    """TEST 1: Verificar imports críticos"""
    print(f"\n{Colors.CYAN}═══ TEST 1: Imports Críticos ═══{Colors.END}")
    
    try:
        from app.services import ocr
        print_test("Import app.services.ocr", True)
    except Exception as e:
        print_test("Import app.services.ocr", False, str(e))
        return False
    
    try:
        from app.services import comparador
        print_test("Import app.services.comparador", True)
    except Exception as e:
        print_test("Import app.services.comparador", False, str(e))
        return False
    
    try:
        from app.services import pdf_generator
        print_test("Import app.services.pdf_generator", True)
    except Exception as e:
        print_test("Import app.services.pdf_generator", False, str(e))
        return False
        
    try:
        from app.db import models
        print_test("Import app.db.models", True)
    except Exception as e:
        print_test("Import app.db.models", False, str(e))
        return False
    
    return True

def test_ocr_functions():
    """TEST 2: Verificar funciones OCR"""
    print(f"\n{Colors.CYAN}═══ TEST 2: Funciones OCR ═══{Colors.END}")
    
    try:
        from app.services.ocr import (
            parse_es_number,
            normalize_text,
            extract_atr,
            extract_potencias,
            _parse_date_flexible
        )
        
        # Test parse_es_number
        assert parse_es_number("1.234,56") == 1234.56
        print_test("parse_es_number('1.234,56')", True, "→ 1234.56")
        
        assert parse_es_number("123,45") == 123.45
        print_test("parse_es_number('123,45')", True, "→ 123.45")
        
        # Test normalize_text
        text = normalize_text("  Hola   Mundo  ")
        assert text == "Hola Mundo"
        print_test("normalize_text", True, f"→ '{text}'")
        
        # Test extract_atr
        atr = extract_atr("Tarifa de acceso: 2.0TD")
        assert atr == "2.0TD"
        print_test("extract_atr", True, f"→ {atr}")
        
        # Test extract_potencias
        result = extract_potencias("Potencia contratada P1: 4.6 kW, P2: 4.6 kW")
        assert result['p1'] == 4.6
        print_test("extract_potencias", True, f"→ P1={result['p1']}, P2={result['p2']}")
        
        return True
        
    except Exception as e:
        print_test("Funciones OCR", False, str(e))
        return False

def test_comparador_functions():
    """TEST 3: Verificar funciones Comparador"""
    print(f"\n{Colors.CYAN}═══ TEST 3: Funciones Comparador ═══{Colors.END}")
    
    try:
        from app.services.comparador import (
            calcular_coste_potencia,
            calcular_coste_energia,
            calcular_impuestos
        )
        
        # Test calcular_coste_potencia
        coste_p = calcular_coste_potencia(4.6, 4.6, 30, 0.10, 0.10)
        assert coste_p > 0
        print_test("calcular_coste_potencia", True, f"→ {coste_p:.2f}€")
        
        # Test calcular_coste_energia
        coste_e = calcular_coste_energia(250, 0, 0, 0.15, 0, 0)
        assert coste_e > 0
        print_test("calcular_coste_energia", True, f"→ {coste_e:.2f}€")
        
        # Test calcular_impuestos
        impuestos = calcular_impuestos(50.0, iva_rate=0.21)
        assert 'impuesto_electrico' in impuestos
        assert 'iva' in impuestos
        print_test("calcular_impuestos", True, f"→ IE={impuestos['impuesto_electrico']:.2f}€, IVA={impuestos['iva']:.2f}€")
        
        return True
        
    except Exception as e:
        print_test("Funciones Comparador", False, str(e))
        return False

def test_database_models():
    """TEST 4: Verificar modelos de base de datos"""
    print(f"\n{Colors.CYAN}═══ TEST 4: Modelos Database ═══{Colors.END}")
    
    try:
        from app.db.models import Factura, Cliente, Oferta
        
        print_test("Modelo Factura", True, "Importado correctamente")
        print_test("Modelo Cliente", True, "Importado correctamente")
        print_test("Modelo Oferta", True, "Importado correctamente")
        
        return True
        
    except Exception as e:
        print_test("Modelos Database", False, str(e))
        return False

def test_file_structure():
    """TEST 5: Verificar estructura de archivos críticos"""
    print(f"\n{Colors.CYAN}═══ TEST 5: Estructura Archivos ═══{Colors.END}")
    
    critical_files = [
        "app/main.py",
        "app/services/ocr.py",
        "app/services/comparador.py",
        "app/services/pdf_generator.py",
        "app/db/models.py",
        "app/routes/webhook.py",
        "requirements.txt",
        "README.md"
    ]
    
    all_exist = True
    for file in critical_files:
        exists = Path(file).exists()
        all_exist = all_exist and exists
        print_test(f"Archivo: {file}", exists)
    
    return all_exist

def test_env_variables():
    """TEST 6: Verificar variables de entorno críticas"""
    print(f"\n{Colors.CYAN}═══ TEST 6: Variables Entorno ═══{Colors.END}")
    
    critical_vars = [
        "DATABASE_URL",
        "GOOGLE_CREDENTIALS"
    ]
    
    all_set = True
    for var in critical_vars:
        exists = os.getenv(var) is not None
        all_set = all_set and exists
        status = "SET" if exists else "NOT SET"
        print_test(f"{var}", exists, status)
    
    return all_set

def test_tarifas_data():
    """TEST 7: Verificar datos de tarifas"""
    print(f"\n{Colors.CYAN}═══ TEST 7: Datos Tarifas ═══{Colors.END}")
    
    try:
        tarifas_dir = Path("tarifas")
        if not tarifas_dir.exists():
            print_test("Directorio tarifas/", False, "No existe")
            return False
        
        json_files = list(tarifas_dir.glob("*.json"))
        print_test(f"Directorio tarifas/", True, f"{len(json_files)} archivos JSON encontrados")
        
        # Intentar cargar un archivo de tarifa
        if json_files:
            sample_file = json_files[0]
            with open(sample_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print_test(f"Cargar {sample_file.name}", True, f"OK - {len(data)} tarifas")
        
        return True
        
    except Exception as e:
        print_test("Datos Tarifas", False, str(e))
        return False

def test_migrations():
    """TEST 8: Verificar migraciones"""
    print(f"\n{Colors.CYAN}═══ TEST 8: Migraciones SQL ═══{Colors.END}")
    
    try:
        migrations_dir = Path("migrations")
        if not migrations_dir.exists():
            print_test("Directorio migrations/", False, "No existe")
            return False
        
        sql_files = list(migrations_dir.glob("*.sql"))
        print_test(f"Directorio migrations/", True, f"{len(sql_files)} archivos SQL encontrados")
        
        return True
        
    except Exception as e:
        print_test("Migraciones", False, str(e))
        return False

def run_all_tests():
    """Ejecutar todos los tests"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 QA POST-CLEANUP - SUITE COMPLETA{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    results = {}
    
    results['imports'] = test_imports()
    results['ocr'] = test_ocr_functions()
    results['comparador'] = test_comparador_functions()
    results['database'] = test_database_models()
    results['files'] = test_file_structure()
    results['env'] = test_env_variables()
    results['tarifas'] = test_tarifas_data()
    results['migrations'] = test_migrations()
    
    # Resumen
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}📊 RESUMEN DE TESTS{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        color = Colors.GREEN if status else Colors.RED
        print(f"{icon} {color}{name.upper()}: {'PASS' if status else 'FAIL'}{Colors.END}")
    
    print(f"\n{Colors.CYAN}Total: {passed}/{total} tests pasados{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}🎉 TODOS LOS TESTS PASARON - OPERATIVA OK{Colors.END}\n")
        return True
    else:
        print(f"\n{Colors.YELLOW}⚠️  Algunos tests fallaron - Revisar detalles arriba{Colors.END}\n")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Tests interrumpidos por usuario{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error fatal: {str(e)}{Colors.END}")
        sys.exit(1)
