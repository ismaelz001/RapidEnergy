import requests

BASE_URL = "https://rapidenergy.onrender.com"
IDS_TO_CLEAN = list(range(62, 80))  # Expanded range

def clean_and_verify():
    print(f"🧹 Limpiando registros ({IDS_TO_CLEAN[0]} - {IDS_TO_CLEAN[-1]})...")
    
    for fid in IDS_TO_CLEAN:
        try:
            r = requests.get(f"{BASE_URL}/webhook/facturas/{fid}")
            if r.status_code == 200:
                data = r.json()
                client_id = data.get("cliente_id")
                
                if client_id:
                    requests.delete(f"{BASE_URL}/clientes/{client_id}")
                else:
                    requests.delete(f"{BASE_URL}/webhook/facturas/{fid}")
                    
        except Exception:
            pass

    print("\n✨ Limpieza completada.")

if __name__ == "__main__":
    clean_and_verify()
