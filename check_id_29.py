from app.db.conn import SessionLocal
from app.db.models import Factura, Cliente
import json

def check_data():
    db = SessionLocal()
    try:
        factura = db.query(Factura).filter(Factura.id == 29).first()
        cliente = db.query(Cliente).filter(Cliente.id == factura.cliente_id).first()
        
        print("--- FACTURA 29 ---")
        print(f"CUPS: {factura.cups}")
        print(f"Importe: {factura.total_factura}")
        print(f"Consumo P1: {factura.consumo_p1_kwh}")
        
        print("\n--- CLIENTE ---")
        print(f"Nombre: {cliente.nombre}")
        print(f"CUPS Cliente: {cliente.cups}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
