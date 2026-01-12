import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.cups import normalize_cups, is_valid_cups

print("=== TEST LOCAL SIMULADO DE VALIDACIÓN CUPS ===\n")
print("Simulando valores que Google Vision extraería de facturas reales...\n")

# Valores que Google Vision OCR extrae de las facturas de prueba
# (Basado en logs de Render que vimos antes)
test_cases = [
    ("f1.jpg", "ESUMEN DE LA FACTURA"),
    ("f2.jpg", "ES0022000008763779TF1P"),
    ("Factura Iberdrola.pdf", "ESVEROCANJEARTUSALDO"),
    ("factura Naturgy.pdf", "ESTARDEACUERDOCONLARE"),
    ("Factura.pdf", "ESUMENDELAFACTURAYDAT"),
    ("Fra Agosto.pdf", "ESTAFACTURANOACREDITAP"),
    ("Fra Gana Agosto.pdf", "ESTUFACTURADEELECTRICI"),
]

print("📊 PROCESANDO FACTURAS...\n")

for filename, cups_raw in test_cases:
    print(f"📄 {filename}")
    print(f"   🔍 OCR extrajo: {cups_raw}")
    
    # Aplicar normalización (como hace el webhook)
    cups_normalized = normalize_cups(cups_raw)
    
    if cups_normalized:
        print(f"   ✅ Normalizado: {cups_normalized}")
        
        # Validar con Mod529
        is_valid = is_valid_cups(cups_normalized)
        if is_valid:
            print(f"   ✅ Válido Mod529: TRUE → CUPS ACEPTADO")
        else:
            print(f"   ❌ Válido Mod529: FALSE → CUPS RECHAZADO")
    else:
        print(f"   ❌ Normalizado: None → RECHAZADO (blacklist o longitud)")
    
    print()

print("\n=== RESULTADO ESPERADO ===")
print("f1.jpg: ESUMENDELAFACTURA → None (blacklist 'FACTURA')")
print("Fra Gana: ESTUFACTURA... → None (blacklist)")
print("Otros sin CUPS real → False en Mod529 (rechazados)")
print("Si algún CUPS es real → True en Mod529 (aceptado)")
