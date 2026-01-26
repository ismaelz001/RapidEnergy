-- ⭐ FIX P0-2: Crear tabla ofertas_calculadas
-- Fecha: 2026-01-19
-- Objetivo: Persistir ofertas generadas por el comparador

CREATE TABLE IF NOT EXISTS ofertas_calculadas (
    id SERIAL PRIMARY KEY,
    comparativa_id INTEGER NOT NULL REFERENCES comparativas(id) ON DELETE CASCADE,
    tarifa_id INTEGER NOT NULL,
    coste_estimado NUMERIC(10, 2),
    ahorro_mensual NUMERIC(10, 2),
    ahorro_anual NUMERIC(10, 2),
    detalle_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_ofertas_calc_comparativa ON ofertas_calculadas(comparativa_id);
CREATE INDEX IF NOT EXISTS idx_ofertas_calc_tarifa ON ofertas_calculadas(tarifa_id);
CREATE INDEX IF NOT EXISTS idx_ofertas_calc_created ON ofertas_calculadas(created_at DESC);

-- Comentarios para documentación
COMMENT ON TABLE ofertas_calculadas IS 'Ofertas persistidas generadas por el comparador';
COMMENT ON COLUMN ofertas_calculadas.comparativa_id IS 'Referencia a la comparativa que generó estas ofertas';
COMMENT ON COLUMN ofertas_calculadas.tarifa_id IS 'ID de la tarifa (de tabla tarifas)';
COMMENT ON COLUMN ofertas_calculadas.coste_estimado IS 'Costo estimado de la oferta para el periodo';
COMMENT ON COLUMN ofertas_calculadas.ahorro_mensual IS 'Ahorro mensual equivalente (proyectado)';
COMMENT ON COLUMN ofertas_calculadas.ahorro_anual IS 'Ahorro anual equivalente (proyectado)';
COMMENT ON COLUMN ofertas_calculadas.detalle_json IS 'JSON completo de la oferta con breakdown';
