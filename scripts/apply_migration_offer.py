#!/usr/bin/env python3
"""
Script para aplicar la migración de selected_offer_json a la base de datos local.
Solo aplica si la columna no existe.
"""
import sqlite3
import sys
import os

DB_PATH = "local.db"

def apply_migration():
    if not os.path.exists(DB_PATH):
        print(f"❌ No se encontró {DB_PATH}")
        sys.exit(1)
    
    print(f"🔄 Conectando a {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar si la columna ya existe
    cursor.execute("PRAGMA table_info(facturas)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "selected_offer_json" in columns:
        print("✅ La columna 'selected_offer_json' ya existe. No es necesario migrar.")
        conn.close()
        return
    
    print("📝 Aplicando migración: Añadiendo columna 'selected_offer_json'...")
    
    try:
        cursor.execute("ALTER TABLE facturas ADD COLUMN selected_offer_json TEXT;")
        conn.commit()
        print("✅ Migración aplicada correctamente.")
        
        # Verificar
        cursor.execute("PRAGMA table_info(facturas)")
        columns = [col[1] for col in cursor.fetchall()]
        if "selected_offer_json" in columns:
            print("✅ Verificación exitosa: columna añadida.")
        else:
            print("⚠️ La columna no apareció en la verificación.")
    except Exception as e:
        print(f"❌ Error al aplicar migración: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    apply_migration()
