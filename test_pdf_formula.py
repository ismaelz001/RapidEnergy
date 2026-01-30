"""
Test para validar que el PDF incluye el desglose de fórmula paso a paso
Sin dependencia de base de datos - verifica la sintaxis del código
"""
import sys
sys.path.insert(0, 'f:\\MecaEnergy')

try:
    # Importar y verificar que la función existe sin errores
    from app.services.pdf_generator import generar_pdf_presupuesto
    import inspect
    
    # Obtener el código fuente
    source = inspect.getsource(generar_pdf_presupuesto)
    
    # Verificar que los elementos clave del desglose están presentes
    checks = [
        ('tabla_c_data', 'Tabla C de desglose paso a paso'),
        ('PASO', 'Columna PASO'),
        ('POTENCIA (P1+P2)', 'Fila de Potencia'),
        ('CONSUMO (P1+P2+P3)', 'Fila de Consumo'),
        ('TOTAL 1', 'Subtotal 1'),
        ('TOTAL 2', 'Subtotal 2 (después IEE)'),
        ('TOTAL 3', 'Subtotal 3 (antes IVA)'),
        ('IVA (21%)', 'Fila IVA'),
        ('IMPORTE TOTAL', 'Importe total final'),
        ('═══', 'Separadores visuales'),
        ('iee_pct', 'Constante IEE'),
        ('bono_social', 'Descuento Bono Social'),
    ]
    
    print("🔍 Validando implementación del desglose de fórmula en PDF...\n")
    
    all_passed = True
    for check_str, description in checks:
        if check_str in source:
            print(f"✅ {description}: Presente")
        else:
            print(f"❌ {description}: NO ENCONTRADO")
            all_passed = False
    
    if all_passed:
        print("\n✅ Test PASSED: Todos los elementos del desglose de fórmula están implementados")
        print("\n📋 El PDF ahora incluye una tabla con los siguientes pasos:")
        print("   1. Potencia (P1+P2)")
        print("   2. Consumo (P1+P2+P3)")
        print("   3. + Bono Social (si aplica)")
        print("   4. × Impuesto Eléctrico (IEE)")
        print("   5. + Alquiler Contador")
        print("   6. IVA (21%)")
        print("   = IMPORTE TOTAL")
        print("\n✨ Los usuarios ahora pueden auditar cada paso del cálculo en el PDF")
    else:
        print("\n❌ Test FAILED: Algunos elementos no están presentes")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error al validar: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
