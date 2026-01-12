-- Migration: Persistir selección de oferta en factura
-- Opción MVP: añadir campo JSON para guardar oferta seleccionada

-- Añadir columna para JSON de oferta seleccionada
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS selected_offer_json TEXT;

-- Actualizar enum de estado para incluir "oferta_seleccionada"
-- (En SQLite no hay ALTER TYPE, pero el campo estado_factura es String así que funciona directamente)

-- Para validar:
-- SELECT id, estado_factura, selected_offer_json FROM facturas WHERE selected_offer_json IS NOT NULL;
