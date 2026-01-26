import os

file_path = "e:/MecaEnergy/app/routes/webhook.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False

pdf_route_start = '@router.get("/facturas/{factura_id}/presupuesto.pdf")'
next_route_start = '@router.delete("/facturas/{factura_id}")'

# La nueva función limpia
clean_pdf_function = [
    '@router.get("/facturas/{factura_id}/presupuesto.pdf")\n',
    'def generar_presupuesto_pdf(factura_id: int, db: Session = Depends(get_db)):\n',
    '    """\n',
    '    PDF con estructura EXACTA: Tabla 1, Tabla 2, Tabla 3 + modelo Patricia Vázquez\n',
    '    """\n',
    '    from fastapi.responses import StreamingResponse\n',
    '    from app.services.pdf_generator import generar_pdf_presupuesto\n',
    '    \n',
    '    factura = db.query(Factura).filter(Factura.id == factura_id).first()\n',
    '    if not factura:\n',
    '        raise HTTPException(status_code=404, detail="Factura no encontrada")\n',
    '    \n',
    '    if not factura.selected_offer_json:\n',
    '        raise HTTPException(status_code=400, detail="No hay una oferta seleccionada.")\n',
    '    \n',
    '    try:\n',
    '        selected_offer = json.loads(factura.selected_offer_json)\n',
    '    except:\n',
    '        raise HTTPException(status_code=500, detail="Error al leer la oferta seleccionada")\n',
    '    \n',
    '    try:\n',
    '        # Generar PDF usando el servicio especializado\n',
    '        buffer = generar_pdf_presupuesto(factura, selected_offer, db)\n',
    '        \n',
    '        return StreamingResponse(\n',
    '            buffer,\n',
    '            media_type="application/pdf",\n',
    '            headers={\n',
    '                "Content-Disposition": f"attachment; filename=presupuesto_energyluz_{factura_id}.pdf",\n',
    '                "Access-Control-Allow-Origin": "*",\n',
    '                "Access-Control-Allow-Methods": "GET, OPTIONS",\n',
    '                "Access-Control-Allow-Headers": "*",\n',
    '            }\n',
    '        )\n',
    '    except Exception as e:\n',
    '        logger.error(f"Error generando PDF: {e}", exc_info=True)\n',
    '        raise HTTPException(status_code=500, detail=f"Error al generar el PDF: {str(e)}")\n',
    '\n',
    '\n'
]

for line in lines:
    if pdf_route_start in line:
        skip = True
        new_lines.extend(clean_pdf_function)
        continue
    
    if skip:
        if next_route_start in line:
            skip = False
            new_lines.append(line)
        continue
    
    new_lines.append(line)

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Webhook cleaning complete!")
