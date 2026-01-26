import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL no encontrada")
    exit(1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Actualizar Iberdrola con precios de potencia
cur.execute("""
    UPDATE tarifas 
    SET potencia_p1_eur_kw_dia = 0.114500,
        potencia_p2_eur_kw_dia = 0.114500
    WHERE id = 1 AND comercializadora = 'Iberdrola'
""")

conn.commit()

print(f"✅ Tarifa Iberdrola actualizada: {cur.rowcount} fila(s) modificada(s)")

# Verificar el cambio
cur.execute("SELECT nombre, potencia_p1_eur_kw_dia, potencia_p2_eur_kw_dia FROM tarifas WHERE id = 1")
result = cur.fetchone()

print(f"\n📊 Tarifa actualizada:")
print(f"   Nombre: {result[0]}")
print(f"   Potencia P1: {result[1]} €/kW·día")
print(f"   Potencia P2: {result[2]} €/kW·día")

cur.close()
conn.close()
