@router.get("/facturas/{factura_id}/presupuesto.pdf")
def generar_presupuesto_pdf(factura_id: int, db: Session = Depends(get_db)):
    """
    GENERACIÓN DE PDF DEFINITIVA
    Llama al servicio especializado que combina un modelo publicitario de `modelosPresuPDF` (p. ej. Estudio EnergyLuz)
    con los datos técnicos (Tablas 1, 2 y 3).
    """
    from fastapi.responses import StreamingResponse
    from app.services.pdf_generator import generar_pdf_presupuesto
    
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if not factura.selected_offer_json:
        raise HTTPException(status_code=400, detail="No hay una oferta seleccionada.")
    
    try:
        selected_offer = json.loads(factura.selected_offer_json)
    except:
        raise HTTPException(status_code=500, detail="Error al leer la oferta seleccionada")
    
    try:
        # Generar PDF usando el servicio especializado
        buffer = generar_pdf_presupuesto(factura, selected_offer, db)
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=presupuesto_energyluz_{factura_id}.pdf",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        logger.error(f"Error generando PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF: {str(e)}")
