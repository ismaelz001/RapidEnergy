import requests
import os

API_URL = "https://rapidenergy.onrender.com/webhook/upload"
FILE_PATH = "e:/MecaEnergy/temp_facturas/facturas/factura Naturgy.pdf"

def test_upload():
    if not os.path.exists(FILE_PATH):
        print(f"Error: No se encuentra el archivo {FILE_PATH}")
        return

    with open(FILE_PATH, "rb") as f:
        files = {"file": ("Factura_Iberdrola.pdf", f, "application/pdf")}
        print(f"Subiendo {FILE_PATH} a {API_URL}...")
        try:
            response = requests.post(API_URL, files=files)
            print(f"Status: {response.status_code}")
            print("Response JSON:")
            import json
            print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_upload()
