import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Conectar a Neon
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL no encontrada")
    exit(1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

# Consultar tarifas
cur.execute("SELECT * FROM tarifas WHERE atr = '2.0TD' LIMIT 5")
tarifas = cur.fetchall()

print(f"📊 Total tarifas 2.0TD en BBDD: {len(tarifas)}\n")

for i, tarifa in enumerate(tarifas, 1):
    print(f"{'='*80}")
    print(f"TARIFA {i}: {tarifa.get('comercializadora')} - {tarifa.get('nombre')}")
    print(f"{'='*80}")
    print(f"  Energía P1: {tarifa.get('energia_p1_eur_kwh')} €/kWh")
    print(f"  Energía P2: {tarifa.get('energia_p2_eur_kwh')} €/kWh")
    print(f"  Energía P3: {tarifa.get('energia_p3_eur_kwh')} €/kWh")
    print(f"  Potencia P1: {tarifa.get('potencia_p1_eur_kw_dia')} €/kW·día")
    print(f"  Potencia P2: {tarifa.get('potencia_p2_eur_kw_dia')} €/kW·día")
    print()

cur.close()
conn.close()
