"""
Script para ejecutar migración 3.0TD en Neon
Usa la conexión configurada en app/db/conn.py
"""

import sys
from sqlalchemy import text
from app.db.conn import engine

def run_migration():
    print("🚀 Iniciando migración 3.0TD...")
    print("=" * 60)
    
    with engine.connect() as conn:
        try:
            # 1. Verificar si existe el campo ATR
            print("\n📋 1. Verificando campo 'atr' en tabla facturas...")
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'facturas' 
                  AND column_name = 'atr'
            """))
            
            if result.fetchone():
                print("   ✅ Campo 'atr' ya existe")
            else:
                print("   ⚠️  Campo 'atr' NO existe, creando...")
                conn.execute(text("""
                    ALTER TABLE facturas 
                    ADD COLUMN atr VARCHAR(10) DEFAULT '2.0TD'
                """))
                conn.commit()
                print("   ✅ Campo 'atr' creado")
            
            # 2. Crear índice
            print("\n📋 2. Creando índice en campo 'atr'...")
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_facturas_atr ON facturas(atr)
                """))
                conn.commit()
                print("   ✅ Índice creado")
            except Exception as e:
                print(f"   ⚠️  Índice ya existe o error: {e}")
            
            # 3. Actualizar ATR según potencia
            print("\n📋 3. Actualizando ATR en facturas existentes...")
            
            # 3.0TD (>= 15kW)
            result = conn.execute(text("""
                UPDATE facturas 
                SET atr = '3.0TD' 
                WHERE potencia_p1_kw >= 15 
                  AND (atr IS NULL OR atr = '2.0TD')
            """))
            count_3td = result.rowcount
            conn.commit()
            print(f"   ✅ {count_3td} facturas marcadas como 3.0TD")
            
            # 2.0TD (< 15kW)
            result = conn.execute(text("""
                UPDATE facturas 
                SET atr = '2.0TD' 
                WHERE potencia_p1_kw < 15 
                  AND (atr IS NULL OR atr != '2.0TD')
            """))
            count_2td = result.rowcount
            conn.commit()
            print(f"   ✅ {count_2td} facturas marcadas como 2.0TD")
            
            # 4. Verificar tabla tarifas
            print("\n📋 4. Verificando tabla 'tarifas'...")
            result = conn.execute(text("""
                SELECT COUNT(*) as total FROM tarifas
            """))
            total = result.fetchone()[0]
            print(f"   ✅ Tabla tarifas existe con {total} tarifas")
            
            # 5. Insertar tarifas 2.0TD si no existen
            print("\n📋 5. Insertando tarifas 2.0TD...")
            
            tarifas_2td = [
                {
                    "nombre": "Tarifa Por Uso Luz",
                    "comercializadora": "Naturgy",
                    "atr": "2.0TD",
                    "tipo": "fija",
                    "e1": 0.120471, "e2": 0.120471, "e3": 0.120471,
                    "p1": 0.111815, "p2": 0.033933,
                    "version": "naturgy_v1"
                },
                {
                    "nombre": "Tarifa Noche Luz ECO",
                    "comercializadora": "Naturgy",
                    "atr": "2.0TD",
                    "tipo": "fija",
                    "e1": 0.190465, "e2": 0.117512, "e3": 0.082673,
                    "p1": 0.111815, "p2": 0.033933,
                    "version": "naturgy_v1"
                },
                {
                    "nombre": "Plan Especial plus 15%TE 1p",
                    "comercializadora": "Iberdrola",
                    "atr": "2.0TD",
                    "tipo": "fija",
                    "e1": 0.127394, "e2": 0.127394, "e3": 0.127394,
                    "p1": 0.073777, "p2": 0.001911,  # BOE 2025
                    "version": "iberdrola_v1"
                },
                {
                    "nombre": "Libre Promo 1er año",
                    "comercializadora": "Endesa",
                    "atr": "2.0TD",
                    "tipo": "fija",
                    "e1": 0.105900, "e2": 0.105900, "e3": 0.105900,
                    "p1": 0.090214, "p2": 0.090214,
                    "permanencia_meses": 12,
                    "version": "endesa_v1"
                },
                {
                    "nombre": "Libre Base",
                    "comercializadora": "Endesa",
                    "atr": "2.0TD",
                    "tipo": "fija",
                    "e1": 0.132375, "e2": 0.132375, "e3": 0.132375,
                    "p1": 0.090214, "p2": 0.090214,
                    "version": "endesa_v1"
                }
            ]
            
            inserted = 0
            for tarifa in tarifas_2td:
                # Verificar si ya existe
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM tarifas 
                    WHERE nombre = :nombre 
                      AND comercializadora = :comercializadora
                """), {
                    "nombre": tarifa["nombre"],
                    "comercializadora": tarifa["comercializadora"]
                })
                
                if result.fetchone()[0] == 0:
                    # Insertar
                    conn.execute(text("""
                        INSERT INTO tarifas (
                            nombre, comercializadora, atr, tipo,
                            energia_p1_eur_kwh, energia_p2_eur_kwh, energia_p3_eur_kwh,
                            potencia_p1_eur_kw_dia, potencia_p2_eur_kw_dia,
                            permanencia_meses, version
                        ) VALUES (
                            :nombre, :comercializadora, :atr, :tipo,
                            :e1, :e2, :e3,
                            :p1, :p2,
                            :permanencia_meses, :version
                        )
                    """), {
                        "nombre": tarifa["nombre"],
                        "comercializadora": tarifa["comercializadora"],
                        "atr": tarifa["atr"],
                        "tipo": tarifa["tipo"],
                        "e1": tarifa["e1"],
                        "e2": tarifa["e2"],
                        "e3": tarifa["e3"],
                        "p1": tarifa["p1"],
                        "p2": tarifa["p2"],
                        "permanencia_meses": tarifa.get("permanencia_meses"),
                        "version": tarifa["version"]
                    })
                    conn.commit()
                    inserted += 1
                    print(f"   ✅ Insertada: {tarifa['comercializadora']} - {tarifa['nombre']}")
                else:
                    print(f"   ⏭️  Ya existe: {tarifa['comercializadora']} - {tarifa['nombre']}")
            
            print(f"\n   📊 Total insertadas: {inserted}/{len(tarifas_2td)}")
            
            # 6. Resumen final
            print("\n" + "=" * 60)
            print("📊 RESUMEN FINAL:")
            print("=" * 60)
            
            # Contar facturas por ATR
            result = conn.execute(text("""
                SELECT atr, COUNT(*) as total
                FROM facturas
                WHERE atr IS NOT NULL
                GROUP BY atr
                ORDER BY atr
            """))
            
            print("\n🗂️  Facturas por ATR:")
            for row in result:
                print(f"   - {row[0]}: {row[1]} facturas")
            
            # Contar tarifas por ATR
            result = conn.execute(text("""
                SELECT atr, COUNT(*) as total
                FROM tarifas
                GROUP BY atr
                ORDER BY atr
            """))
            
            print("\n💰 Tarifas por ATR:")
            for row in result:
                print(f"   - {row[0]}: {row[1]} tarifas")
            
            print("\n" + "=" * 60)
            print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
            print("=" * 60)
            print("\n📝 Próximos pasos:")
            print("   1. Obtener tarifas 3.0TD del PO")
            print("   2. Insertar tarifas 3.0TD en la base de datos")
            print("   3. Probar comparador con factura >= 15kW")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        sys.exit(1)
