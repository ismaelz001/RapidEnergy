import requests
import sys

BASE_URL = "https://rapidenergy.onrender.com"
TARGET_ID = 56

def nuke_target():
    print(f"🎯 Buscando y destruyendo Factura ID {TARGET_ID}...")
    try:
        # 1. Obtener info para ver si tiene cliente
        r = requests.get(f"{BASE_URL}/webhook/facturas/{TARGET_ID}")
        if r.status_code == 200:
            data = r.json()
            client_id = data.get("cliente_id")
            
            if client_id:
                print(f"   🔥 Factura tiene cliente {client_id}. Borrando CLIENTE (Cascada)...")
                del_r = requests.delete(f"{BASE_URL}/clientes/{client_id}")
                print(f"   Cliente Delete Status: {del_r.status_code}")
            else:
                print(f"   🔥 Factura huérfana. Borrando FACTURA directamente...")
                del_r = requests.delete(f"{BASE_URL}/webhook/facturas/{TARGET_ID}")
                print(f"   Factura Delete Status: {del_r.status_code}")
                
        elif r.status_code == 404:
            print("   ⚠️ La factura ya no existe.")
        else:
            print(f"   ❌ Error consultando: {r.status_code}")

    except Exception as e:
        print(f"   ❌ Excepción: {e}")

if __name__ == "__main__":
    nuke_target()
