-- Migration to add DATE columns to 'facturas' table
-- IMPORTANT: Run this if you haven't already, otherwise saving invoices will fail!

ALTER TABLE facturas ADD COLUMN fecha_inicio TEXT;
ALTER TABLE facturas ADD COLUMN fecha_fin TEXT;

-- Verify all new columns
-- \d facturas
