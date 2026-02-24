-- Script para limpiar clientes huérfanos (sin comercial_id o company_id asignado)
-- ⚠️ EJECUTAR EN NEON CONSOLE DESPUÉS DE HACER BACKUP

-- 1. Ver clientes huérfanos (sin comercial ni company)
SELECT id, nombre, cups, origen, created_at, comercial_id, company_id 
FROM clientes 
WHERE comercial_id IS NULL OR company_id IS NULL
ORDER BY created_at DESC;

-- 2. ELIMINAR clientes huérfanos (CUIDADO - NO REVERSIBLE)
-- Descomentar la línea siguiente solo si estás seguro:
-- DELETE FROM clientes WHERE comercial_id IS NULL OR company_id IS NULL;

-- 3. Verificar que no quedan huérfanos
SELECT COUNT(*) as clientes_huerfanos FROM clientes WHERE comercial_id IS NULL OR company_id IS NULL;
