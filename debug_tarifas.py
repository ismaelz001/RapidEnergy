from app.db.conn import SessionLocal
from sqlalchemy import text
import json

def check_tarifas():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT count(*) FROM tarifas"))
        count = result.scalar()
        print(f"Total tarifas: {count}")
        
        result = db.execute(text("SELECT * FROM tarifas LIMIT 5"))
        tarifas = [dict(row._mapping) for row in result.fetchall()]
        print("Muestra de tarifas:")
        print(json.dumps(tarifas, indent=2, default=str))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_tarifas()
