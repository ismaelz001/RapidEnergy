import requests
import json

API_URL = "https://rapidenergy.onrender.com/webhook/facturas"

def verify_recent():
    try:
        response = requests.get(API_URL)
        if response.status_code != 200:
            print(f"Error fetching invoices: {response.status_code}")
            return

        facturas = response.json()
        # Sort by ID descending if not already
        facturas.sort(key=lambda x: x['id'], reverse=True)
        
        print(f"Total facturas found: {len(facturas)}")
        print("--- Last 5 Invoices ---")
        
        for f in facturas[:5]:
            cliente_nombre = "N/A"
            if f.get('cliente'):
                cliente_nombre = f['cliente'].get('nombre', 'N/A')
            
            print(f"ID: {f['id']}")
            print(f"  CUPS: {f.get('cups')}")
            print(f"  Cliente: {cliente_nombre}")
            print(f"  Total: {f.get('total_factura')}")
            print(f"  Fecha: {f.get('fecha')}")
            print("-" * 20)

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    verify_recent()
