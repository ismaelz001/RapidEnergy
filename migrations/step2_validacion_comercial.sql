-- ============================================
-- MIGRACIÓN: STEP 2 - Validación Comercial
-- ============================================
-- Fecha: 2026-01-26
-- Objetivo: Añadir campos para validación comercial antes de comparar
-- ============================================

-- 1. Añadir columnas para Step 2
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS ajustes_comerciales_json TEXT;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS total_ajustado DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS validado_step2 BOOLEAN DEFAULT FALSE;

-- 2. Crear índice para búsquedas
CREATE INDEX IF NOT EXISTS idx_facturas_validado_step2 ON facturas(validado_step2);

-- 3. Comentarios para documentación
COMMENT ON COLUMN facturas.ajustes_comerciales_json IS 'JSON con ajustes comerciales aplicados (Bono Social, descuentos, servicios)';
COMMENT ON COLUMN facturas.total_ajustado IS 'Total calculado después de excluir conceptos no comparables (cifra reina)';
COMMENT ON COLUMN facturas.validado_step2 IS 'TRUE si la factura pasó por validación comercial';

-- ============================================
-- CONSULTAS DE VERIFICACIÓN
-- ============================================

-- Ver facturas validadas en Step 2
SELECT id, estado_factura, total_factura, total_ajustado, validado_step2
FROM facturas
WHERE validado_step2 = TRUE
LIMIT 10;

-- Ver diferencias entre total original y ajustado
SELECT 
    id,
    total_factura AS original,
    total_ajustado AS ajustado,
    (total_ajustado - total_factura) AS diferencia,
    ROUND(((total_ajustado - total_factura) / total_factura * 100), 2) AS pct_cambio
FROM facturas
WHERE validado_step2 = TRUE AND total_ajustado IS NOT NULL
ORDER BY pct_cambio DESC
LIMIT 10;

-- ============================================
-- ROLLBACK (si algo sale mal)
-- ============================================

-- Eliminar columnas
-- ALTER TABLE facturas DROP COLUMN IF EXISTS ajustes_comerciales_json;
-- ALTER TABLE facturas DROP COLUMN IF EXISTS total_ajustado;
-- ALTER TABLE facturas DROP COLUMN IF EXISTS validado_step2;

-- Eliminar índice
-- DROP INDEX IF EXISTS idx_facturas_validado_step2;
