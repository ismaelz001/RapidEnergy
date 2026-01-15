import requests

# Actualizar vía API (necesitarás crear un endpoint temporal o hacerlo manualmente en Neon)
print("⚠️ No se puede actualizar directamente desde local sin DATABASE_URL")
print("\n📋 SOLUCIÓN MANUAL:")
print("\n1. Ve a Neon Console: https://console.neon.tech/")
print("2. Abre tu proyecto RapidEnergy")
print("3. Ve a SQL Editor")
print("4. Ejecuta esta query:\n")

query = """
UPDATE tarifas 
SET potencia_p1_eur_kw_dia = 0.114500,
    potencia_p2_eur_kw_dia = 0.114500
WHERE id = 1 AND comercializadora = 'Iberdrola';

-- Verificar el cambio
SELECT id, nombre, comercializadora, 
       potencia_p1_eur_kw_dia, potencia_p2_eur_kw_dia 
FROM tarifas 
WHERE id = 1;
"""

print(query)
print("\n✅ Después de ejecutar, la tarifa de Iberdrola tendrá los precios de potencia completos.")
