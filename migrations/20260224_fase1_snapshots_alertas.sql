-- ============================================
-- FASE 1: SNAPSHOTS MENSUALES + ALERTAS RENOVACIÓN
-- Fecha: 2026-02-24
-- ============================================

-- ===== TABLA 1: SNAPSHOTS MENSUALES =====
-- Guarda el estado del sistema cada mes (día 1)
CREATE TABLE IF NOT EXISTS snapshots_mensuales (
    id SERIAL PRIMARY KEY,
    periodo DATE NOT NULL,  -- Ejemplo: '2026-02-01' (siempre día 1 del mes)
    tipo VARCHAR(50) NOT NULL,  -- 'clientes_activos', 'comisiones_pendientes', 'renovaciones_proximas'
    data JSONB NOT NULL,  -- Datos del snapshot en formato JSON
    total_registros INTEGER DEFAULT 0,  -- Contador rápido para KPIs
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Índices para consultas rápidas
    CONSTRAINT unique_periodo_tipo UNIQUE (periodo, tipo)
);

CREATE INDEX idx_snapshots_periodo ON snapshots_mensuales(periodo);
CREATE INDEX idx_snapshots_tipo ON snapshots_mensuales(tipo);
CREATE INDEX idx_snapshots_created ON snapshots_mensuales(created_at);

COMMENT ON TABLE snapshots_mensuales IS 'Snapshots mensuales para auditoría y reporting histórico';
COMMENT ON COLUMN snapshots_mensuales.periodo IS 'Periodo del snapshot (siempre día 1 del mes)';
COMMENT ON COLUMN snapshots_mensuales.tipo IS 'Tipo: clientes_activos, comisiones_pendientes, renovaciones_proximas';
COMMENT ON COLUMN snapshots_mensuales.data IS 'Datos JSON del snapshot (flexible)';


-- ===== TABLA 2: ALERTAS RENOVACIÓN =====
-- Sistema de recordatorios para renovaciones de clientes
CREATE TABLE IF NOT EXISTS alertas_renovacion (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    comercial_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Fechas críticas
    fecha_contrato DATE NOT NULL,  -- Fecha de alta del contrato
    fecha_alerta DATE NOT NULL,  -- Fecha cuando debe saltar alerta (contrato + 270 días = 9 meses)
    fecha_renovacion_estimada DATE NOT NULL,  -- Fecha estimada de renovación (contrato + 365 días)
    
    -- Estado de la alerta
    estado VARCHAR(20) DEFAULT 'pendiente',  -- pendiente, gestionada, renovada, perdida, cancelada
    prioridad VARCHAR(20) DEFAULT 'normal',  -- baja, normal, alta, urgente
    
    -- Seguimiento
    notas TEXT,
    gestionada_at TIMESTAMP WITH TIME ZONE,
    resultado VARCHAR(50),  -- 'renovado_misma_tarifa', 'renovado_mejor_tarifa', 'perdido_competencia', etc.
    
    -- Auditoría
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,  -- Soft delete
    
    -- Constraints
    CHECK (estado IN ('pendiente', 'gestionada', 'renovada', 'perdida', 'cancelada')),
    CHECK (prioridad IN ('baja', 'normal', 'alta', 'urgente'))
);

CREATE INDEX idx_alertas_cliente ON alertas_renovacion(cliente_id);
CREATE INDEX idx_alertas_comercial ON alertas_renovacion(comercial_id);
CREATE INDEX idx_alertas_fecha_alerta ON alertas_renovacion(fecha_alerta);
CREATE INDEX idx_alertas_estado ON alertas_renovacion(estado);
CREATE INDEX idx_alertas_deleted ON alertas_renovacion(deleted_at);

COMMENT ON TABLE alertas_renovacion IS 'Sistema de alertas para renovaciones de contratos';
COMMENT ON COLUMN alertas_renovacion.fecha_alerta IS 'Fecha en que debe alertarse (9 meses desde contrato)';
COMMENT ON COLUMN alertas_renovacion.estado IS 'pendiente: sin gestionar | gestionada: contactado | renovada: éxito | perdida: churn';


-- ===== TABLA 3: TAREAS AUTOMÁTICAS =====
-- Registro de tareas generadas automáticamente para seguimiento
CREATE TABLE IF NOT EXISTS tareas_clientes (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    comercial_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Detalles de la tarea
    tipo VARCHAR(50) NOT NULL,  -- 'seguimiento_inicial', 'verificar_activacion', 'check_primer_mes', 'renovacion'
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    fecha_programada DATE NOT NULL,
    
    -- Estado
    estado VARCHAR(20) DEFAULT 'pendiente',  -- pendiente, en_proceso, completada, cancelada
    prioridad VARCHAR(20) DEFAULT 'normal',
    
    -- Resultado
    completada_at TIMESTAMP WITH TIME ZONE,
    notas_resultado TEXT,
    
    -- Auditoría
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CHECK (estado IN ('pendiente', 'en_proceso', 'completada', 'cancelada')),
    CHECK (prioridad IN ('baja', 'normal', 'alta', 'urgente')),
    CHECK (tipo IN ('seguimiento_inicial', 'verificar_activacion', 'check_primer_mes', 'check_trimestral', 'renovacion'))
);

CREATE INDEX idx_tareas_cliente ON tareas_clientes(cliente_id);
CREATE INDEX idx_tareas_comercial ON tareas_clientes(comercial_id);
CREATE INDEX idx_tareas_fecha ON tareas_clientes(fecha_programada);
CREATE INDEX idx_tareas_estado ON tareas_clientes(estado);
CREATE INDEX idx_tareas_tipo ON tareas_clientes(tipo);

COMMENT ON TABLE tareas_clientes IS 'Tareas automáticas de seguimiento de clientes';


-- ===== FUNCIÓN: AUTO-CREAR ALERTAS AL CREAR CLIENTE =====
-- Trigger para crear alerta de renovación automáticamente
CREATE OR REPLACE FUNCTION crear_alerta_renovacion()
RETURNS TRIGGER AS $$
BEGIN
    -- Solo crear alerta si el cliente está en estado "contratado" o "activo"
    IF NEW.estado IN ('contratado', 'activo') AND NEW.deleted_at IS NULL THEN
        INSERT INTO alertas_renovacion (
            cliente_id,
            comercial_id,
            fecha_contrato,
            fecha_alerta,
            fecha_renovacion_estimada,
            estado
        ) VALUES (
            NEW.id,
            NEW.comercial_id,
            CURRENT_DATE,
            CURRENT_DATE + INTERVAL '270 days',  -- 9 meses
            CURRENT_DATE + INTERVAL '365 days',  -- 12 meses
            'pendiente'
        )
        ON CONFLICT DO NOTHING;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger
DROP TRIGGER IF EXISTS trigger_crear_alerta_renovacion ON clientes;
CREATE TRIGGER trigger_crear_alerta_renovacion
    AFTER INSERT OR UPDATE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION crear_alerta_renovacion();


-- ===== FUNCIÓN: AUTO-CREAR TAREAS AL CREAR CLIENTE =====
CREATE OR REPLACE FUNCTION crear_tareas_seguimiento()
RETURNS TRIGGER AS $$
BEGIN
    -- Solo crear tareas si el cliente está "contratado" o "activo"
    IF NEW.estado IN ('contratado', 'activo') AND NEW.deleted_at IS NULL THEN
        
        -- Tarea 1: Seguimiento inicial (día siguiente)
        INSERT INTO tareas_clientes (
            cliente_id,
            comercial_id,
            tipo,
            titulo,
            descripcion,
            fecha_programada,
            prioridad
        ) VALUES (
            NEW.id,
            NEW.comercial_id,
            'seguimiento_inicial',
            'Seguimiento inicial - ' || NEW.nombre,
            'Contactar cliente para confirmar alta y resolver dudas',
            CURRENT_DATE + INTERVAL '1 day',
            'alta'
        );
        
        -- Tarea 2: Verificar activación (7 días)
        INSERT INTO tareas_clientes (
            cliente_id,
            comercial_id,
            tipo,
            titulo,
            descripcion,
            fecha_programada,
            prioridad
        ) VALUES (
            NEW.id,
            NEW.comercial_id,
            'verificar_activacion',
            'Verificar activación - ' || NEW.nombre,
            'Confirmar que el servicio está activo y funcionando correctamente',
            CURRENT_DATE + INTERVAL '7 days',
            'normal'
        );
        
        -- Tarea 3: Check primer mes (30 días)
        INSERT INTO tareas_clientes (
            cliente_id,
            comercial_id,
            tipo,
            titulo,
            descripcion,
            fecha_programada,
            prioridad
        ) VALUES (
            NEW.id,
            NEW.comercial_id,
            'check_primer_mes',
            'Revisión primer mes - ' || NEW.nombre,
            'Verificar primera factura y satisfacción del cliente',
            CURRENT_DATE + INTERVAL '30 days',
            'normal'
        );
        
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger
DROP TRIGGER IF EXISTS trigger_crear_tareas_seguimiento ON clientes;
CREATE TRIGGER trigger_crear_tareas_seguimiento
    AFTER INSERT ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION crear_tareas_seguimiento();


-- ===== VISTA: ALERTAS ACTIVAS (Para dashboard) =====
CREATE OR REPLACE VIEW v_alertas_activas AS
SELECT 
    a.id,
    a.cliente_id,
    c.nombre AS cliente_nombre,
    c.email AS cliente_email,
    c.cups,
    a.comercial_id,
    u.name AS comercial_nombre,
    a.fecha_contrato,
    a.fecha_alerta,
    a.fecha_renovacion_estimada,
    a.estado,
    a.prioridad,
    a.notas,
    -- Días hasta renovación
    (a.fecha_renovacion_estimada - CURRENT_DATE) AS dias_hasta_renovacion,
    -- Flag urgente (menos de 60 días)
    CASE 
        WHEN (a.fecha_renovacion_estimada - CURRENT_DATE) <= 60 THEN true
        ELSE false
    END AS es_urgente,
    a.created_at
FROM alertas_renovacion a
JOIN clientes c ON a.cliente_id = c.id
LEFT JOIN users u ON a.comercial_id = u.id
WHERE a.deleted_at IS NULL
  AND a.estado IN ('pendiente', 'gestionada')
  AND c.deleted_at IS NULL
ORDER BY a.fecha_alerta ASC;

COMMENT ON VIEW v_alertas_activas IS 'Vista de alertas pendientes o en gestión (para dashboard)';


-- ===== VISTA: TAREAS PENDIENTES SEMANA =====
CREATE OR REPLACE VIEW v_tareas_semana AS
SELECT 
    t.id,
    t.cliente_id,
    c.nombre AS cliente_nombre,
    c.estado AS cliente_estado,
    t.comercial_id,
    u.name AS comercial_nombre,
    t.tipo,
    t.titulo,
    t.descripcion,
    t.fecha_programada,
    t.estado,
    t.prioridad,
    -- Semana ISO
    EXTRACT(ISOYEAR FROM t.fecha_programada) AS año,
    EXTRACT(WEEK FROM t.fecha_programada) AS semana,
    -- Día de la semana (1=Lunes, 7=Domingo)
    EXTRACT(ISODOW FROM t.fecha_programada) AS dia_semana,
    t.created_at
FROM tareas_clientes t
JOIN clientes c ON t.cliente_id = c.id
LEFT JOIN users u ON t.comercial_id = u.id
WHERE t.deleted_at IS NULL
  AND t.estado IN ('pendiente', 'en_proceso')
  AND c.deleted_at IS NULL
  -- Tareas de próximas 4 semanas
  AND t.fecha_programada BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '28 days'
ORDER BY t.fecha_programada ASC, t.prioridad DESC;

COMMENT ON VIEW v_tareas_semana IS 'Tareas de las próximas 4 semanas para agenda semanal';


-- ===== DATOS DE EJEMPLO (Opcional - comentar en producción) =====
-- Insertar snapshot de prueba
INSERT INTO snapshots_mensuales (periodo, tipo, data, total_registros)
VALUES (
    '2026-02-01',
    'clientes_activos',
    '{"total_clientes": 45, "nuevos_mes": 12, "bajas_mes": 3, "churn_rate": 6.67}'::jsonb,
    45
);

-- ===== VERIFICACIÓN =====
SELECT 'Tablas creadas correctamente:' AS mensaje;
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('snapshots_mensuales', 'alertas_renovacion', 'tareas_clientes');

SELECT 'Vistas creadas correctamente:' AS mensaje;
SELECT table_name FROM information_schema.views 
WHERE table_schema = 'public' 
AND table_name IN ('v_alertas_activas', 'v_tareas_semana');

SELECT 'Triggers creados correctamente:' AS mensaje;
SELECT trigger_name FROM information_schema.triggers 
WHERE trigger_schema = 'public' 
AND trigger_name IN ('trigger_crear_alerta_renovacion', 'trigger_crear_tareas_seguimiento');
