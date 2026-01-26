-- P1: Periodo obligatorio + tabla Comparativas

-- 1. Añadir periodo_dias a facturas
ALTER TABLE facturas ADD COLUMN periodo_dias INTEGER;

-- 2. Crear tabla comparativas
CREATE TABLE IF NOT EXISTS comparativas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factura_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    periodo_dias INTEGER,
    current_total REAL,
    inputs_json TEXT,
    offers_json TEXT,
    status VARCHAR DEFAULT 'ok',
    error_json TEXT,
    FOREIGN KEY (factura_id) REFERENCES facturas(id)
);

-- Para Postgres (cuando deploys a Neon):
-- ALTER TABLE facturas ADD COLUMN IF NOT EXISTS periodo_dias INTEGER;
-- CREATE TABLE IF NOT EXISTS comparativas (...);  -- igual estructura
