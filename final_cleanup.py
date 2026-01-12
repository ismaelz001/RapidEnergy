import requests

BASE_URL = "https://rapidenergy.onrender.com"
IDS_TO_CLEAN = [32, 33, 34, 35, 36, 37]

def clean_and_verify():
    print("🧹 Limpiando registros sucios de pruebas anteriores...")
    
    for fid in IDS_TO_CLEAN:
        # Primero obtenemos el cliente para borrarlo en cascada
        try:
            r = requests.get(f"{BASE_URL}/webhook/facturas/{fid}")
            if r.status_code == 200:
                data = r.json()
                client_id = data.get("cliente_id") or (data.get("cliente") or {}).get("id")
                
                if client_id:
                    print(f"   Deleting Client {client_id} (linked to Factura {fid})...")
                    requests.delete(f"{BASE_URL}/clientes/{client_id}")
                else:
                    print(f"   Deleting Orphan Factura {fid}...")
                    requests.delete(f"{BASE_URL}/webhook/facturas/{fid}")
            else:
                print(f"   Factura {fid} not found (maybe already deleted).")
                
        except Exception as e:
            print(f"   Error cleaning {fid}: {e}")

    print("\n✨ Limpieza completada. Ahora puedes probar subida limpia.")

if __name__ == "__main__":
    clean_and_verify()
