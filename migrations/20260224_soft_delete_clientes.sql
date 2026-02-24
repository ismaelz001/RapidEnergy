-- ============================================================
-- MIGRACIÓN: Soft Delete para Clientes
-- Fecha: 2026-02-24
-- Descripción: Añade columna deleted_at para borrado lógico
-- ============================================================

ALTER TABLE clientes 
ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

CREATE INDEX idx_clientes_deleted_at ON clientes(deleted_at);

COMMENT ON COLUMN clientes.deleted_at IS 'Soft delete: NULL = activo, NOT NULL = eliminado';
