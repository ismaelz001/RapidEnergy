import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.db.conn import SessionLocal
from app.db.models import Factura
from app.services.ocr import parse_invoice_text

def repair_invoices():
    db: Session = SessionLocal()
    try:
        facturas = db.query(Factura).all()
        print(f"Checking {len(facturas)} invoices for repair...")
        
        updated_count = 0
        for f in facturas:
            if not f.raw_data:
                continue
            
            try:
                raw_json = json.loads(f.raw_data)
                raw_text = raw_json.get("raw_text")
            except:
                raw_text = f.raw_data # Fallback if stored as plain text
                
            if not raw_text or len(raw_text) < 50:
                continue
                
            print(f"Reparsing Factura #{f.id} ({f.filename})...")
            new_data = parse_invoice_text(raw_text)
            
            changes = []
            
            # Helper to update if better
            def update_if_new(field, db_field_name=None):
                db_name = db_field_name or field
                curr_val = getattr(f, db_name)
                new_val = new_data.get(field)
                
                # Update if current is None/0 and new is valid
                should_update = (curr_val is None or curr_val == 0) and new_val is not None
                
                # Special case: Total Factura priority
                if field == "total_factura":
                    # If current is seemingly Base Imponible (e.g. < new_val) update it
                    if curr_val and new_val and new_val > curr_val:
                        should_update = True
                
                if should_update:
                    setattr(f, db_name, new_val)
                    changes.append(f"{db_name}: {curr_val} -> {new_val}")

            update_if_new("cups")
            update_if_new("atr")
            update_if_new("total_factura")
            update_if_new("fecha_inicio_consumo", "fecha_inicio")
            update_if_new("fecha_fin_consumo", "fecha_fin")
            
            # Consumptions & Powers
            for k in ["p1", "p2", "p3", "p4", "p5", "p6"]:
                update_if_new(f"consumo_p{k}_kwh")
            
            update_if_new("potencia_p1_kw")
            update_if_new("potencia_p2_kw")
            
            # Save dias_facturados to raw_data if found
            if new_data.get("dias_facturados"):
                try:
                    current_raw = json.loads(f.raw_data)
                except:
                    current_raw = {"raw_text": f.raw_data}
                
                if "parsed_fields" not in current_raw:
                    current_raw["parsed_fields"] = {}
                
                current_raw["parsed_fields"]["dias_facturados"] = new_data["dias_facturados"]
                f.raw_data = json.dumps(current_raw, ensure_ascii=False)
                changes.append(f"raw_data.dias_facturados -> {new_data['dias_facturados']}")

            if changes:
                print(f"  [FIXED] {', '.join(changes)}")
                updated_count += 1
            else:
                print("  [OK] No improved data found.")
                
        if updated_count > 0:
            db.commit()
            print(f"\nSuccessfully repaired {updated_count} invoices.")
        else:
            print("\nNo changes needed.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    repair_invoices()
