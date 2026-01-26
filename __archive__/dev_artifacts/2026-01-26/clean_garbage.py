import requests

API_URL = "https://rapidenergy.onrender.com/webhook/facturas/30"

def delete_garbage():
    print(f"Borrando factura basura ID 30...")
    try:
        response = requests.delete(API_URL)
        if response.status_code == 200:
            print("✅ ID 30 Eliminada con éxito.")
        else:
            print(f"❌ Fallo al eliminar: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Excepción: {e}")

if __name__ == "__main__":
    delete_garbage()
