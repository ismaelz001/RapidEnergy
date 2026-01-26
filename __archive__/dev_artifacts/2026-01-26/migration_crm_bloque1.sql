-- ⭐ BLOQUE 1 MVP CRM: Migraciones para Companies, Users y columnas nuevas
-- Ejecutar en Neon (PostgreSQL)

-- 1. Crear tabla companies
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    nif VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Crear tabla users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    role VARCHAR NOT NULL CHECK (role IN ('dev', 'ceo', 'comercial')),
    company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_company_id ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 3. Agregar columna comercial_id a clientes
ALTER TABLE clientes 
ADD COLUMN IF NOT EXISTS comercial_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_clientes_comercial_id ON clientes(comercial_id);

-- 4. Agregar columnas de selección de oferta a facturas
ALTER TABLE facturas 
ADD COLUMN IF NOT EXISTS selected_oferta_id BIGINT REFERENCES ofertas_calculadas(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS selected_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS selected_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_facturas_selected_oferta_id ON facturas(selected_oferta_id);
CREATE INDEX IF NOT EXISTS idx_facturas_selected_by_user_id ON facturas(selected_by_user_id);

-- 5. Comentar selected_offer_json como deprecated (no eliminar por backward compatibility)
COMMENT ON COLUMN facturas.selected_offer_json IS 'Deprecated: usar selected_oferta_id en su lugar';

-- 6. Insertar usuario dev por defecto (CAMBIAR PASSWORD EN PRODUCCIÓN)
INSERT INTO users (email, name, role, company_id, is_active)
VALUES ('dev@mecaenergy.com', 'Dev Admin', 'dev', NULL, TRUE)
ON CONFLICT (email) DO NOTHING;

COMMIT;
