import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

def reset_local_db():
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ Error: No se ha encontrado DATABASE_URL en el .env")
        return

    # --- PROTECCIÓN ANTI-PRODUCCIÓN ---
    remoto_keywords = ["neon.tech", "render.com", "rds.amazonaws.com"]
    if any(k in database_url for k in remoto_keywords):
        print("🛑 ¡ALTO! Se ha detectado una base de datos REMOTA / PRODUCCIÓN.")
        print(f"URL: {database_url}")
        print("Este script solo puede ejecutarse contra una base de datos LOCAL (SQLite o Local Postgres).")
        sys.exit(1)

    print(f"⚠️ Reseteando base de datos local: {database_url}")
    print("Confirmas que quieres BORRAR TODOS los datos de Clientes y Facturas locales? (s/n)")
    
    # En un entorno no interactivo como este, asumimos confirmación si pasamos una flag o similar,
    # pero para el usuario pediremos el comando manual.
    confirm = input().lower() if sys.stdin.isatty() else "s"
    
    if confirm != 's':
        print("Operación cancelada.")
        return

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Desactivar constraints temporalmente para limpieza fácil
            if "sqlite" in database_url:
                conn.execute(text("PRAGMA foreign_keys = OFF;"))
                tables = ["facturas", "clientes"]
                for table in tables:
                    try:
                        conn.execute(text(f"DELETE FROM {table};"))
                        print(f"✅ Tabla {table} vaciada.")
                    except Exception as e:
                        print(f"⚠️ No se pudo vaciar {table}: {e}")
                conn.execute(text("PRAGMA foreign_keys = ON;"))
            else:
                # Postgres local
                conn.execute(text("TRUNCATE TABLE facturas, clientes CASCADE;"))
                print("✅ Tablas vaciadas (TRUNCATE CASCADE).")
            
            conn.commit()
        print("\n✨ Base de datos local limpia y lista para nuevos tests.")
        
    except Exception as e:
        print(f"❌ Error durante el reset: {e}")

if __name__ == "__main__":
    reset_local_db()
