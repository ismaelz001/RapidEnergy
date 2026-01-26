-- Añadir campo iva_porcentaje a facturas
-- Ejecutar en SQL Editor de Neon

ALTER TABLE facturas 
ADD COLUMN IF NOT EXISTS iva_porcentaje DOUBLE PRECISION;

COMMENT ON COLUMN facturas.iva_porcentaje IS 'Porcentaje de IVA aplicado (21, 10, 4)';

-- Actualizar valores existentes basados en el importe de IVA (si existe)
-- Esto es opcional, solo para migrar datos históricos
UPDATE facturas
SET iva_porcentaje = 21
WHERE iva_porcentaje IS NULL AND iva IS NOT NULL;
