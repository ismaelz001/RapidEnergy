#!/usr/bin/env python3
"""
Script para actualizar clientes que tienen datos NULL desde las facturas
"""

import sys
sys.path.insert(0, '.')

from app.db.models import Cliente, Factura
from app.db.conn import SessionLocal
from app.services.ocr import extract_data_from_pdf
from app.utils.cups import normalize_cups

db = SessionLocal()

print("=" * 80)
print("ACTUALIZAR CLIENTES CON DATOS DE FACTURAS")
print("=" * 80)

try:
    # Encontrar clientes con datos NULL que tengan facturas
    clientes_null = db.query(Cliente).filter(
        (Cliente.nombre == None) |
        (Cliente.dni == None) |
        (Cliente.direccion == None)
    ).all()
    
    print(f"\nEncontrados {len(clientes_null)} clientes con datos incompletos\n")
    
    for cliente in clientes_null:
        print(f"Cliente #{cliente.id}:")
        print(f"  CUPS: {cliente.cups}")
        print(f"  Nombre: {cliente.nombre}")
        print(f"  DNI: {cliente.dni}")
        print(f"  Dirección: {cliente.direccion}")
        
        # Buscar facturas de este cliente
        if cliente.cups:
            facturas = db.query(Factura).filter(Factura.cups == cliente.cups).all()
            print(f"  Facturas encontradas: {len(facturas)}")
            
            if facturas:
                # Usar la primera factura para rellenar datos
                factura = facturas[0]
                
                # Extraer datos de la factura
                try:
                    import json
                    raw_data = json.loads(factura.raw_data) if factura.raw_data else {}
                    
                    # Buscar datos en raw_data
                    nombre = raw_data.get('titular') or raw_data.get('nombre')
                    dni = raw_data.get('dni')
                    direccion = raw_data.get('direccion')
                    telefono = raw_data.get('telefono')
                    provincia = raw_data.get('provincia')
                    
                    # Actualizar cliente
                    updated = False
                    if not cliente.nombre and nombre:
                        cliente.nombre = nombre
                        updated = True
                        print(f"  ✅ Nombre actualizado: {nombre}")
                    
                    if not cliente.dni and dni:
                        cliente.dni = dni
                        updated = True
                        print(f"  ✅ DNI actualizado: {dni}")
                    
                    if not cliente.direccion and direccion:
                        cliente.direccion = direccion
                        updated = True
                        print(f"  ✅ Dirección actualizada: {direccion}")
                    
                    if not cliente.telefono and telefono:
                        cliente.telefono = telefono
                        updated = True
                        print(f"  ✅ Teléfono actualizado: {telefono}")
                    
                    if not cliente.provincia and provincia:
                        cliente.provincia = provincia
                        updated = True
                        print(f"  ✅ Provincia actualizada: {provincia}")
                    
                    if updated:
                        db.commit()
                        print(f"  💾 Cliente #{cliente.id} actualizado en BD")
                    else:
                        print(f"  ⚠️ No hay datos nuevos para actualizar")
                
                except Exception as e:
                    print(f"  ❌ Error extrayendo datos: {e}")
        else:
            print(f"  ⚠️ Sin CUPS, no se puede buscar facturas")
        
        print()
    
    # Mostrar resultado final
    print("=" * 80)
    print("CLIENTES ACTUALIZADOS")
    print("=" * 80)
    
    clientes_updated = db.query(Cliente).all()
    for cliente in clientes_updated:
        if cliente.nombre or cliente.dni or cliente.direccion:
            print(f"\n✅ Cliente #{cliente.id}:")
            print(f"   Nombre: {cliente.nombre}")
            print(f"   DNI: {cliente.dni}")
            print(f"   CUPS: {cliente.cups}")
            print(f"   Teléfono: {cliente.telefono}")
            print(f"   Dirección: {cliente.direccion}")

finally:
    db.close()
