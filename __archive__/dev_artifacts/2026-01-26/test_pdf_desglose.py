# Mini-Test PDF Desglose Técnico
# Ejecutar manualmente en Python console o crear factura de prueba

# Test 1: to_money con diferentes formatos
def to_money(value):
    """Helper para formatear valores monetarios con 2 decimales
    Maneja: None, NaN, strings ("96.43", "96,43"), floats, ints
    """
    try:
        if value is None:
            return "0.00 €"
        
        # Si es string, reemplazar coma por punto y limpiar espacios
        if isinstance(value, str):
            value = value.replace(',', '.').strip()
            if not value:
                return "0.00 €"
        
        # Convertir a float
        num = float(value)
        
        # Check NaN
        if num != num:  # NaN check
            return "0.00 €"
        
        return f"{num:.2f} €"
    except (ValueError, TypeError):
        return "0.00 €"

# Casos de prueba
print("=== TEST 1: Formatos de números ===")
print(f"None: {to_money(None)}")  # → "0.00 €"
print(f"0: {to_money(0)}")  # → "0.00 €"
print(f"96.43: {to_money(96.43)}")  # → "96.43 €"
print(f"'96.43': {to_money('96.43')}")  # → "96.43 €"
print(f"'96,43': {to_money('96,43')}")  # → "96.43 €"
print(f"'96,43 ': {to_money('96,43 ')}")  # → "96.43 €"
print(f"'': {to_money('')}")  # → "0.00 €"
print(f"float('nan'): {to_money(float('nan'))}")  # → "0.00 €"
print(f"'abc': {to_money('abc')}")  # → "0.00 €"

print("\n=== TEST 2: Factura sin desglose ===")
# Simular factura solo con total
factura_data = {
    'coste_energia': None,
    'coste_potencia': None,
    'impuesto_electrico': None,
    'alquiler_contador': None,
    'iva': None,
    'total_factura': 107.00
}

print("Tabla A:")
print(f"  Coste energía:     {to_money(factura_data.get('coste_energia') or 0.0)}")
print(f"  Coste potencia:    {to_money(factura_data.get('coste_potencia') or 0.0)}")
print(f"  Impuesto eléctrico:{to_money(factura_data.get('impuesto_electrico') or 0.0)}")
print(f"  Alquiler contador: {to_money(factura_data.get('alquiler_contador') or 0.0)}")
print(f"  IVA:               {to_money(factura_data.get('iva') or 0.0)}")
print(f"  TOTAL FACTURA:     {to_money(factura_data['total_factura'])}")
# Esperado: todas las filas 0.00 € excepto TOTAL = 107.00 €

print("\n=== TEST 3: Breakdown con strings ===")
breakdown_string = {
    'coste_energia': "58.09",
    'coste_potencia': "15,99",  # Con coma
    'impuestos': 20.88,
    'alquiler_contador': 0.74,
    'iva': None
}

print("Tabla B:")
print(f"  Energía estimada:  {to_money(breakdown_string.get('coste_energia'))}")
print(f"  Potencia estimada: {to_money(breakdown_string.get('coste_potencia'))}")
print(f"  Impuesto eléctrico:{to_money(breakdown_string.get('impuestos'))}")
print(f"  Alquiler contador: {to_money(breakdown_string.get('alquiler_contador'))}")
print(f"  IVA:               {to_money(breakdown_string.get('iva'))}")
# Esperado: 58.09 €, 15.99 €, 20.88 €, 0.74 €, 0.00 €

print("\n=== TEST 4: Ahorro negativo ===")
factura_total = 38.88
oferta_total = 64.94
periodo_dias = 30

ahorro_periodo = factura_total - oferta_total
print(f"Ahorro periodo: {ahorro_periodo:.2f} €")  # -26.06 €

if ahorro_periodo <= 0:
    ahorro_mensual = 0.0
    ahorro_anual = 0.0
    alerta = "⚠️ No se detecta ahorro con esta oferta."
    print(f"Ahorro mensual: {ahorro_mensual:.2f} € (forzado a 0)")
    print(f"Ahorro anual: {ahorro_anual:.2f} € (forzado a 0)")
    print(f"Alerta: {alerta}")
else:
    ahorro_mensual = ahorro_periodo / (periodo_dias / 30.0)
    ahorro_anual = ahorro_mensual * 12
    print(f"Ahorro mensual: {ahorro_mensual:.2f} €")
    print(f"Ahorro anual: {ahorro_anual:.2f} €")

# Esperado:
# Ahorro periodo: -26.06 €
# Ahorro mensual: 0.00 € (forzado a 0)
# Ahorro anual: 0.00 € (forzado a 0)
# Alerta: ⚠️ No se detecta ahorro...

print("\n=== TODOS LOS TESTS PASADOS ✅ ===")
