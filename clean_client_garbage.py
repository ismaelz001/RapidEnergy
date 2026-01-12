import requests
import json

def get_garbage_details():
    try:
        # Get factura details
        r = requests.get("https://rapidenergy.onrender.com/webhook/facturas/30")
        data = r.json()
        print("--- Factura 30 ---")
        print(json.dumps(data, indent=2))
        
        if 'cliente' in data and data['cliente']:
            client_id = data['cliente']['id']
            print(f"\nDetectado Cliente ID: {client_id}")
            
            # Delete client
            print(f"Borrando Cliente {client_id} (y factura en cascada)...")
            del_r = requests.delete(f"https://rapidenergy.onrender.com/clientes/{client_id}")
            print(f"Delete Status: {del_r.status_code}")
            print(del_r.text)

    except Exception as e:
        print(e)

if __name__ == "__main__":
    get_garbage_details()
