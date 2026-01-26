-- P1 PRODUCCIÓN: Migración para Neon Postgres
-- Ejecutar en SQL Editor de Neon

-- 1. Añadir campo periodo_dias a facturas
ALTER TABLE facturas 
ADD COLUMN IF NOT EXISTS periodo_dias INTEGER;

-- 2. Crear tabla comparativas
CREATE TABLE IF NOT EXISTS comparativas (
    id SERIAL PRIMARY KEY,
    factura_id INTEGER NOT NULL REFERENCES facturas(id) ON DELETE CASCADE,
    periodo_dias INTEGER NOT NULL,
    current_total NUMERIC(10, 2),
    inputs_json JSONB,
    offers_json JSONB,
    status VARCHAR(20) DEFAULT 'ok',
    error_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Crear índices para performance
CREATE INDEX IF NOT EXISTS idx_comparativas_factura_id ON comparativas(factura_id);
CREATE INDEX IF NOT EXISTS idx_comparativas_created_at ON comparativas(created_at DESC);

-- 4. Comentarios para documentación
COMMENT ON TABLE comparativas IS 'P1: Auditoría de comparaciones de ofertas';
COMMENT ON COLUMN comparativas.periodo_dias IS 'Periodo real usado en la comparación (días)';
COMMENT ON COLUMN comparativas.inputs_json IS 'Snapshot de inputs de la factura';
COMMENT ON COLUMN comparativas.offers_json IS 'Resultado completo del comparador';
