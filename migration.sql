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

-- Crear índice único para CUPS (si no existe ya por la primary key o logica implícita)
CREATE UNIQUE INDEX IF NOT EXISTS ix_clientes_cups ON clientes (cups);

-- 2. Añadir relación a facturas (si no existe la columna)
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS cliente_id INTEGER REFERENCES clientes(id);

-- Opcional: Crear índice para la foreign key para mejorar rendimiento
CREATE INDEX IF NOT EXISTS ix_facturas_cliente_id ON facturas (cliente_id);
