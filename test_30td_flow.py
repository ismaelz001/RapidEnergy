
import os
import json
from sqlalchemy import text
from app.db.conn import engine, SessionLocal
from app.db.models import Factura, Cliente
from app.services.comparador import compare_factura

def test_30td_flow():
    db = SessionLocal()
    print("🚀 Iniciando Test de Flujo 3.0TD...")
    
    try:
        # 1. Crear un cliente de prueba
        cliente = Cliente(
            nombre="Empresa Test S.L.",
            email="empresa@test.com",
            cups="ES0021000000000000003TD"
        )
        db.add(cliente)
        db.commit()
        db.refresh(cliente)

        # 2. Crear una factura 3.0TD ficticia
        # Potencia > 15kW obliga al comparador a usar modo 3.0TD
        factura_3td = Factura(
            cliente_id=cliente.id,
            filename="factura_industrial_test.pdf",
            total_factura=850.40,
            periodo_dias=30,
            atr="3.0TD",
            # Potencias (P1-P6) - Todas >= 15kW
            potencia_p1_kw=25.0,
            potencia_p2_kw=25.0,
            potencia_p3_kw=25.0,
            potencia_p4_kw=25.0,
            potencia_p5_kw=25.0,
            potencia_p6_kw=25.0,
            # Consumos (P1-P6) - Repartidos
            consumo_p1_kwh=500.0,
            consumo_p2_kwh=450.0,
            consumo_p3_kwh=600.0,
            consumo_p4_kwh=400.0,
            consumo_p5_kwh=300.0,
            consumo_p6_kwh=800.0,
            estado_factura="datos_listos"
        )
        db.add(factura_3td)
        db.commit()
        db.refresh(factura_3td)
        
        print(f"✅ Factura 3.0TD creada (ID: {factura_3td.id}, Potencia: {factura_3td.potencia_p1_kw}kW)")

        # 3. Ejecutar la comparación
        print("\n🧠 Ejecutando comparador...")
        resultado = compare_factura(factura_3td, db)
        
        # 4. Analizar resultados
        print("\n📊 RESULTADOS DE LA COMPARATIVA:")
        print(f"Factura Original: {resultado['current_total']}€")
        print(f"Periodo: {resultado['periodo_dias']} días")
        print(f"Ofertas encontradas: {len(resultado['offers'])}")
        
        for i, offer in enumerate(resultado['offers']):
            print(f"\n--- Oferta {i+1}: {offer['provider']} - {offer['plan_name']} ---")
            print(f"Total Estimado: {offer['estimated_total']}€")
            print(f"Ahorro Mensual: {offer['ahorro_mensual_equiv']}€")
            print(f"Modo Potencia: {offer['breakdown']['modo_potencia']}")
            print(f"Impuestos: {offer['breakdown']['impuestos']}€")
            
            # Verificar si el IVA es 21% (obligatorio en 3.0TD)
            if offer['breakdown']['modo_iva'] == "calculado_21%_3.0TD":
                print("✅ IVA 21% aplicado correctamente (Modo Industrial)")
            else:
                print(f"❌ ERROR: IVA incorrecto ({offer['breakdown']['modo_iva']})")

    except Exception as e:
        print(f"❌ Error en el test: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_30td_flow()
