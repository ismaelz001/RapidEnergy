import requests
import os
import json

API_URL = "https://rapidenergy.onrender.com/webhook/upload"
DIR_PATH = "e:/MecaEnergy/temp_facturas/facturas"

def mass_upload():
    if not os.path.exists(DIR_PATH):
        print(f"Directory not found: {DIR_PATH}")
        return

    files = [f for f in os.listdir(DIR_PATH) if os.path.isfile(os.path.join(DIR_PATH, f))]
    
    print(f"🚀 Iniciando prueba masiva con {len(files)} facturas...")
    print("-" * 60)

    results = []

    for filename in files:
        file_path = os.path.join(DIR_PATH, filename)
        print(f"\n📄 Procesando: {filename} ...")
        
        try:
            with open(file_path, "rb") as f:
                # Determinate mime type roughly
                mime_type = "application/pdf"
                if filename.lower().endswith((".jpg", ".jpeg")):
                    mime_type = "image/jpeg"
                elif filename.lower().endswith(".png"):
                    mime_type = "image/png"

                upload_files = {"file": (filename, f, mime_type)}
                response = requests.post(API_URL, files=upload_files)

                if response.status_code == 200:
                    data = response.json()
                    ocr = data.get("ocr_preview", {})
                    
                    engine = ocr.get("ocr_engine", "Unknown/Vision")
                    cups = ocr.get("cups")
                    cliente = ocr.get("titular") or ocr.get("cliente")
                    total = ocr.get("total_factura") or ocr.get("importe")
                    
                    print(f"   ✅ ÉXITO (ID: {data.get('id')})")
                    print(f"      Motor Used: {engine}")
                    print(f"      CUPS:       {cups}")
                    print(f"      Cliente:    {cliente}")
                    print(f"      Total:      {total} €")
                    
                    results.append({
                        "file": filename,
                        "status": "OK",
                        "engine": engine,
                        "cups": cups,
                        "client": cliente
                    })
                    
                elif response.status_code == 409:
                    err = response.json().get("detail", {})
                    print(f"   ⚠️ DUPLICADA (ID Existente: {err.get('id')})")
                    print(f"      Mensaje: {err.get('message')}")
                    results.append({"file": filename, "status": "DUPLICATE"})
                
                else:
                    print(f"   ❌ ERROR {response.status_code}")
                    print(f"      {response.text[:200]}")
                    results.append({"file": filename, "status": "ERROR"})

        except Exception as e:
            print(f"   ❌ EXCEPCIÓN: {e}")
            results.append({"file": filename, "status": "EXCEPTION"})

    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    for r in results:
        status_icon = "✅" if r['status'] == "OK" else ("⚠️" if r['status'] == "DUPLICATE" else "❌")
        info = ""
        if r['status'] == "OK":
            info = f"| {r['engine']} | CUPS: {r['cups']} | Client: {r['client']}"
        print(f"{status_icon} {r['file']:<25} {r['status']:<10} {info}")

if __name__ == "__main__":
    mass_upload()
