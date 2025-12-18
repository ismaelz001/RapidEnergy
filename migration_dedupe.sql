-- Migration to add deduplication columns to 'facturas' table

-- 1. Add file_hash column (used for SHA256 file duplicate check)
ALTER TABLE facturas ADD COLUMN file_hash TEXT;
CREATE UNIQUE INDEX idx_facturas_file_hash ON facturas(file_hash);

-- 2. Add numero_factura column (used for semantic duplicate check)
ALTER TABLE facturas ADD COLUMN numero_factura TEXT;

-- Verify changes
-- \d facturas
