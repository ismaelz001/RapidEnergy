import os
import sys
import json
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.db.conn import get_db

# Ensure we can import app
sys.path.append(os.getcwd())

# Load Google Creds if present
if os.path.exists("google_creds.json"):
    print("🔑 Loading google_creds.json into GOOGLE_CREDENTIALS env var...")
    with open("google_creds.json", "r") as f:
        os.environ["GOOGLE_CREDENTIALS"] = f.read()

client = TestClient(app)

def run_qa():
    print("🚀 Starting QA in PRODUCTION MODE (Real OCR + Real DB)")
    
    # 1. Upload Invoice
    filename = "facturas/xfactura_09.jpg"
    if not os.path.exists(filename):
        # Fallback to first jpg found
        for root, dirs, files in os.walk("facturas"):
            for f in files:
                if f.endswith(".jpg") or f.endswith(".png"):
                    filename = os.path.join(root, f)
                    break
            if filename != "facturas/xfactura_10.jpg": break
            
    print(f"📄 Using invoice: {filename}")
    
    upload_resp = None
    factura_id = None
    
    with open(filename, "rb") as f:
        response = client.post(
            "/webhook/upload",
            files={"file": (os.path.basename(filename), f, "image/jpeg")}
        )
        upload_resp = response.json()
        print("\n--- [STEP 1] UPLOAD RESPONSE ---")
        print(json.dumps(upload_resp, indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            factura_id = upload_resp["id"]
        elif response.status_code == 409: # Duplicate
             print("⚠️ Invoice already exists (Duplicate). Using existing ID.")
             factura_id = upload_resp["detail"]["id"] # Adjust based on actual 409 body structure
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return

    if not factura_id:
        print("❌ No Factura ID obtained.")
        return

    # 2. PUT with Missing Fields (Force Incomplete)
    print(f"\n--- [STEP 2] PUT (Incomplete Data) on ID {factura_id} ---")
    payload_incomplete = {
        "potencia_p1_kw": None, # Force missing
        "atr": "2.0TD" # Ensure this is present so we only miss p1
    }
    put_resp = client.put(f"/webhook/facturas/{factura_id}", json=payload_incomplete)
    print(json.dumps(put_resp.json(), indent=2, ensure_ascii=False))

    # 3. POST Comparar (Expect Error)
    print(f"\n--- [STEP 3] POST COMPARAR (Expect Failure) on ID {factura_id} ---")
    comp_resp = client.post(f"/webhook/comparar/facturas/{factura_id}")
    try:
        print(json.dumps(comp_resp.json(), indent=2, ensure_ascii=False))
    except:
        print(comp_resp.text)

    # 4. SQL Check
    print(f"\n--- [STEP 4] DATABASE STATUS ---")
    db = next(get_db())
    query = text("SELECT id, atr, potencia_p1_kw, potencia_p2_kw, consumo_p1_kwh, consumo_p2_kwh, consumo_p3_kwh, total_factura, estado_factura FROM facturas WHERE id = :id")
    result = db.execute(query, {"id": factura_id}).first()
    
    if result:
        # Convert row to dict for printing
        row_dict = result._mapping
        print(dict(row_dict))
    else:
        print("❌ Record not found in DB")

if __name__ == "__main__":
    run_qa()
