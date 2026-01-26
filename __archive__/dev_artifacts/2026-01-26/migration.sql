-- 1. Crear tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR,
    email VARCHAR,
    telefono VARCHAR,
    dni VARCHAR,
    cups VARCHAR,
    direccion VARCHAR,
    provincia VARCHAR,
    estado VARCHAR DEFAULT 'lead',
    origen VARCHAR DEFAULT 'factura_upload',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indice unico para CUPS
CREATE UNIQUE INDEX IF NOT EXISTS ix_clientes_cups ON clientes (cups);

-- 2. Relacion facturas -> clientes
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS cliente_id INTEGER REFERENCES clientes(id);
CREATE INDEX IF NOT EXISTS ix_facturas_cliente_id ON facturas (cliente_id);

-- 3. Nuevos campos de factura para comparacion energetica
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS potencia_p1_kw DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS potencia_p2_kw DOUBLE PRECISION;

ALTER TABLE facturas ADD COLUMN IF NOT EXISTS consumo_p1_kwh DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS consumo_p2_kwh DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS consumo_p3_kwh DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS consumo_p4_kwh DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS consumo_p5_kwh DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS consumo_p6_kwh DOUBLE PRECISION;

ALTER TABLE facturas ADD COLUMN IF NOT EXISTS bono_social BOOLEAN DEFAULT FALSE;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS servicios_vinculados BOOLEAN DEFAULT FALSE;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS alquiler_contador DOUBLE PRECISION;

ALTER TABLE facturas ADD COLUMN IF NOT EXISTS impuesto_electrico DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS iva DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS total_factura DOUBLE PRECISION;

ALTER TABLE facturas ADD COLUMN IF NOT EXISTS estado_factura VARCHAR DEFAULT 'pendiente_datos';
