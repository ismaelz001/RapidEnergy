-- ═══════════════════════════════════════════════════════════════════════════════
-- MIGRACIONES: Módulo Gestión CRM - Sistema de Casos
-- ═══════════════════════════════════════════════════════════════════════════════
-- Fecha: 10 Febrero 2026
-- Objetivo: Añadir gestión de casos comerciales sin romper el sistema actual
-- ═══════════════════════════════════════════════════════════════════════════════
-- INSTRUCCIONES:
-- 1. Ejecutar cada bloque UNO POR UNO en Neon
-- 2. Verificar el resultado después de cada bloque
-- 3. Si hay error, NO continuar hasta resolverlo
-- ═══════════════════════════════════════════════════════════════════════════════


-- ═══════════════════════════════════════════════════════════════════════════════
-- BLOQUE 1: Crear tabla casos
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS casos (
    id BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    
    -- Relaciones
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    asesor_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    colaborador_id INTEGER REFERENCES colaboradores(id) ON DELETE SET NULL,
    
    -- Datos del contrato
    cups VARCHAR(255),
    direccion_suministro TEXT,
    tarifa_contratada VARCHAR(50),
    potencia_contratada DOUBLE PRECISION,
    comercializadora VARCHAR(255),  -- "Endesa", "Repsol", etc (NO FK a companies)
    
    -- Pipeline comercial
    estado_comercial VARCHAR(50) NOT NULL DEFAULT 'lead',
    
    -- Fechas del pipeline
    fecha_contacto TIMESTAMP WITH TIME ZONE,
    fecha_propuesta TIMESTAMP WITH TIME ZONE,
    fecha_firma TIMESTAMP WITH TIME ZONE,
    fecha_activacion TIMESTAMP WITH TIME ZONE,
    fecha_baja TIMESTAMP WITH TIME ZONE,
    
    -- Oferta seleccionada
    oferta_calculada_id BIGINT REFERENCES ofertas_calculadas(id) ON DELETE SET NULL,
    ahorro_estimado_anual DOUBLE PRECISION,
    
    -- Origen
    origen VARCHAR(50) DEFAULT 'manual',
    factura_origen_id INTEGER REFERENCES facturas(id) ON DELETE SET NULL,
    
    -- Notas y seguimiento
    notas TEXT,
    prioridad VARCHAR(20) DEFAULT 'normal',
    
    -- Auditoría
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- ⏸️ PAUSA: Verificar que la tabla se creó correctamente
-- SELECT * FROM casos LIMIT 1;


-- ═══════════════════════════════════════════════════════════════════════════════
-- BLOQUE 2: Crear índices para casos
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_casos_cliente_id ON casos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_casos_asesor_user_id ON casos(asesor_user_id);
CREATE INDEX IF NOT EXISTS idx_casos_colaborador_id ON casos(colaborador_id);
CREATE INDEX IF NOT EXISTS idx_casos_estado_comercial ON casos(estado_comercial);
CREATE INDEX IF NOT EXISTS idx_casos_cups ON casos(cups);
CREATE INDEX IF NOT EXISTS idx_casos_codigo ON casos(codigo);
CREATE INDEX IF NOT EXISTS idx_casos_created_at ON casos(created_at DESC);

-- ⏸️ PAUSA: Verificar índices
-- SELECT indexname FROM pg_indexes WHERE tablename = 'casos';


-- ═══════════════════════════════════════════════════════════════════════════════
-- BLOQUE 3: Añadir caso_id a comisiones_generadas
-- ═══════════════════════════════════════════════════════════════════════════════

-- Añadir columna caso_id
ALTER TABLE comisiones_generadas 
ADD COLUMN IF NOT EXISTS caso_id BIGINT REFERENCES casos(id) ON DELETE SET NULL;

-- Crear índice para caso_id
CREATE INDEX IF NOT EXISTS idx_comisiones_caso_id ON comisiones_generadas(caso_id);

-- ⏸️ PAUSA: Verificar columna añadida
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'comisiones_generadas' AND column_name = 'caso_id';


-- ═══════════════════════════════════════════════════════════════════════════════
-- BLOQUE 4: Documentar estados válidos de comisiones
-- ═══════════════════════════════════════════════════════════════════════════════

-- Estados actuales: pendiente, validada, pagada, anulada
-- Estados NUEVOS: retenida, decomision

-- Añadir comentario para documentar
COMMENT ON COLUMN comisiones_generadas.estado IS 
'Estados válidos: pendiente, validada, pagada, anulada, retenida, decomision';

-- Verificar estados actuales en uso
SELECT DISTINCT estado, COUNT(*) 
FROM comisiones_generadas 
GROUP BY estado;

-- ⏸️ NOTA: Los nuevos estados (retenida, decomision) se validarán en la API


-- ═══════════════════════════════════════════════════════════════════════════════
-- BLOQUE 5: Crear tabla historial_caso
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS historial_caso (
    id BIGSERIAL PRIMARY KEY,
    caso_id BIGINT NOT NULL REFERENCES casos(id) ON DELETE CASCADE,
    
    tipo_evento VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    
    estado_anterior VARCHAR(50),
    estado_nuevo VARCHAR(50),
    
    metadata_json TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_historial_caso_caso_id ON historial_caso(caso_id);
CREATE INDEX IF NOT EXISTS idx_historial_caso_created_at ON historial_caso(created_at DESC);

-- ⏸️ PAUSA: Verificar tabla creada
-- SELECT * FROM historial_caso LIMIT 1;


-- ═══════════════════════════════════════════════════════════════════════════════
-- BLOQUE 6: Migrar datos existentes (clientes → casos)
-- ═══════════════════════════════════════════════════════════════════════════════

-- ⚠️ CUIDADO: Este script crea UN CASO por cada CLIENTE existente
-- Si un cliente tiene múltiples facturas/contratos, solo creará uno
-- Luego podrás crear casos adicionales manualmente

INSERT INTO casos (
    codigo,
    cliente_id,
    asesor_user_id,
    cups,
    estado_comercial,
    origen,
    factura_origen_id,
    created_at
)
SELECT
    CONCAT('CASO-', EXTRACT(YEAR FROM c.created_at), '-', LPAD(ROW_NUMBER() OVER (ORDER BY c.id)::TEXT, 4, '0')) AS codigo,
    c.id AS cliente_id,
    c.comercial_id AS asesor_user_id,  -- ⚠️ comercial_id en clientes apunta a users.id
    c.cups,
    CASE
        WHEN c.estado = 'contratado' THEN 'activo'
        WHEN c.estado = 'oferta_enviada' THEN 'propuesta_enviada'
        WHEN c.estado = 'seguimiento' THEN 'contactado'
        WHEN c.estado = 'descartado' THEN 'perdido'
        ELSE 'lead'
    END AS estado_comercial,
    'migracion_automatica' AS origen,
    (SELECT f.id FROM facturas f WHERE f.cliente_id = c.id ORDER BY f.created_at DESC LIMIT 1) AS factura_origen_id,
    c.created_at
FROM clientes c
WHERE NOT EXISTS (SELECT 1 FROM casos WHERE casos.cliente_id = c.id);

-- ⏸️ PAUSA: Verificar migración
-- SELECT COUNT(*) AS total_clientes FROM clientes;
-- SELECT COUNT(*) AS total_casos FROM casos;
-- (Deberían coincidir si es la primera migración)


-- ═══════════════════════════════════════════════════════════════════════════════
-- BLOQUE 7: Crear eventos iniciales en historial
-- ═══════════════════════════════════════════════════════════════════════════════

INSERT INTO historial_caso (caso_id, tipo_evento, descripcion, created_at)
SELECT
    id AS caso_id,
    'creacion' AS tipo_evento,
    'Caso creado automáticamente desde migración de datos' AS descripcion,
    created_at
FROM casos
WHERE origen = 'migracion_automatica'
  AND NOT EXISTS (SELECT 1 FROM historial_caso hc WHERE hc.caso_id = casos.id);

-- ⏸️ PAUSA: Verificar historial
-- SELECT COUNT(*) FROM historial_caso;


-- ═══════════════════════════════════════════════════════════════════════════════
-- BLOQUE 8: Vincular comisiones existentes a casos
-- ═══════════════════════════════════════════════════════════════════════════════

-- Actualizar caso_id en comisiones_generadas existentes
UPDATE comisiones_generadas cg
SET caso_id = (
    SELECT cas.id
    FROM casos cas
    INNER JOIN facturas f ON f.cliente_id = cas.cliente_id
    WHERE f.id = cg.factura_id
    LIMIT 1
)
WHERE cg.caso_id IS NULL
  AND EXISTS (
    SELECT 1
    FROM casos cas
    INNER JOIN facturas f ON f.cliente_id = cas.cliente_id
    WHERE f.id = cg.factura_id
  );

-- ⏸️ PAUSA: Verificar vinculación
-- SELECT 
--     COUNT(*) FILTER (WHERE caso_id IS NOT NULL) AS con_caso,
--     COUNT(*) FILTER (WHERE caso_id IS NULL) AS sin_caso
-- FROM comisiones_generadas;


-- ═══════════════════════════════════════════════════════════════════════════════
-- VERIFICACIÓN FINAL
-- ═══════════════════════════════════════════════════════════════════════════════

-- 1. Resumen de casos creados
SELECT 
    estado_comercial,
    COUNT(*) AS cantidad,
    COUNT(DISTINCT cliente_id) AS clientes_unicos
FROM casos
GROUP BY estado_comercial
ORDER BY cantidad DESC;

-- 2. Casos sin cliente (no debería haber)
SELECT COUNT(*) AS casos_huerfanos
FROM casos
WHERE cliente_id NOT IN (SELECT id FROM clientes);

-- 3. Comisiones sin caso (normales si son antiguas)
SELECT COUNT(*) AS comisiones_sin_caso
FROM comisiones_generadas
WHERE caso_id IS NULL;

-- 4. Verificar estructura completa
SELECT 
    'clientes' AS tabla, COUNT(*) AS registros FROM clientes
UNION ALL
SELECT 'casos', COUNT(*) FROM casos
UNION ALL
SELECT 'comisiones_generadas', COUNT(*) FROM comisiones_generadas
UNION ALL
SELECT 'historial_caso', COUNT(*) FROM historial_caso;

-- 5. Ver casos de ejemplo
SELECT 
    cas.codigo,
    cli.nombre AS cliente_nombre,
    u.name AS asesor_nombre,
    cas.estado_comercial,
    cas.cups,
    cas.comercializadora,
    cas.created_at
FROM casos cas
INNER JOIN clientes cli ON cli.id = cas.cliente_id
LEFT JOIN users u ON u.id = cas.asesor_user_id
ORDER BY cas.created_at DESC
LIMIT 10;


-- ═══════════════════════════════════════════════════════════════════════════════
-- ROLLBACK (Solo si algo sale MAL)
-- ═══════════════════════════════════════════════════════════════════════════════

-- ⚠️ USAR SOLO EN CASO DE EMERGENCIA

-- DROP TABLE IF EXISTS historial_caso CASCADE;
-- DROP TABLE IF EXISTS casos CASCADE;
-- ALTER TABLE comisiones_generadas DROP COLUMN IF EXISTS caso_id;


-- ═══════════════════════════════════════════════════════════════════════════════
-- FIN DE MIGRACIONES
-- ═══════════════════════════════════════════════════════════════════════════════
