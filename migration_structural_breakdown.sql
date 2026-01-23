-- ============================================
-- MIGRACIÓN: Desglose Estructural Baseline
-- ============================================
-- Agrega columnas para persistir E_actual y P_actual
-- indispensable para el PDF de presupuesto.

ALTER TABLE facturas 
ADD COLUMN IF NOT EXISTS coste_energia_actual DOUBLE PRECISION;

ALTER TABLE facturas 
ADD COLUMN IF NOT EXISTS coste_potencia_actual DOUBLE PRECISION;

COMMENT ON COLUMN facturas.coste_energia_actual IS 'Coste neto energía (E) de la factura analizada';
COMMENT ON COLUMN facturas.coste_potencia_actual IS 'Coste neto potencia (P) de la factura analizada';
