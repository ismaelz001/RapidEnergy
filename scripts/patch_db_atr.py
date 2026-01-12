import os
import sys
from sqlalchemy import text
from app.db.conn import engine

def patch_db():
    print(f"🔧 Check DB URL: {engine.url}")
    print("🔧 Patching DB: Adding 'atr' column...")
    with engine.connect() as conn:
        try:
            # Try generic SQL first
            conn.execute(text("ALTER TABLE facturas ADD COLUMN atr VARCHAR;"))
            conn.commit()
            print("✅ DB Patched (atr added).")
        except Exception as e:
            print(f"⚠️ Patch attempted: {e}")
            # Ignore if column exists
            pass

if __name__ == "__main__":
    patch_db()
