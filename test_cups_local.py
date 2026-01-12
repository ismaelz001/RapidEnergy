from app.utils.cups import normalize_cups, is_valid_cups

print("=== TEST LOCAL DE VALIDACIÓN CUPS ===\n")

# Casos de prueba
test_cases = [
    ("ESUMENDELAFACTURA", "Basura con 'FACTURA' en blacklist"),
    ("ESTUFACTURADEELECTRICI", "Basura con 'FACTURA' y 'ELECTRICIDAD'"),
    ("ESTARDEACUERDOCONLARE", "Basura sin blacklist pero corto"),
    ("ES0022000008763779TF1P", "CUPS real válido (20 chars)"),
    ("ES0022000008763779TF", "CUPS corto (18 chars, inválido)"),
    ("ES00220000087637791234", "CUPS largo (24 chars, inválido)"),
]

for cups_input, descripcion in test_cases:
    print(f"📋 Input: {cups_input}")
    print(f"   Descripción: {descripcion}")
    
    # Normalizar
    normalized = normalize_cups(cups_input)
    print(f"   ✅ Normalizado: {normalized}")
    
    # Si pasó normalización, validar Mod529
    if normalized:
        is_valid = is_valid_cups(normalized)
        print(f"   🔢 Validación Mod529: {is_valid}")
    else:
        print(f"   ❌ Rechazado en normalización (None)")
    
    print()

print("\n=== RESULTADO ESPERADO ===")
print("✅ ESUMENDELAFACTURA → None (blacklist)")
print("✅ ESTUFACTURA... → None (blacklist)")
print("✅ ESTARDE... → None (longitud < 20)")
print("✅ ES0022...TF1P → Validado (si pasa Mod529)")
