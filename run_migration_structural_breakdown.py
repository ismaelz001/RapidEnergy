import sys
from sqlalchemy import text
from app.db.conn import engine

def run_migration():
    print("🚀 Ejecutando migración: Desglose Estructural Baseline...")
    print("=" * 60)
    
    with engine.connect() as conn:
        try:
            # 1. Agregar coste_energia_actual
            print("\n📋 1. Agregando columna 'coste_energia_actual'...")
            conn.execute(text("""
                ALTER TABLE facturas 
                ADD COLUMN IF NOT EXISTS coste_energia_actual DOUBLE PRECISION
            """))
            conn.commit()
            print("   ✅ OK")
            
            # 2. Agregar coste_potencia_actual
            print("\n📋 2. Agregando columna 'coste_potencia_actual'...")
            conn.execute(text("""
                ALTER TABLE facturas 
                ADD COLUMN IF NOT EXISTS coste_potencia_actual DOUBLE PRECISION
            """))
            conn.commit()
            print("   ✅ OK")
            
            print("\n" + "=" * 60)
            print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    run_migration()
