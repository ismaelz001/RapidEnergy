-- ============================================
-- ACTUALIZACIÓN BASE DE DATOS - Soporte 3.0TD
-- ============================================
-- Fecha: 2026-01-15
-- Objetivo: Preparar BBDD para tarifas 3.0TD
-- ============================================

-- NOTA: Los campos P4/P5/P6 YA EXISTEN en la tabla facturas
-- Solo necesitamos agregar el campo 'atr' para identificar el tipo

-- ============================================
-- 1. AGREGAR CAMPO ATR A FACTURAS (si no existe)
-- ============================================

-- Verificar si existe el campo
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'facturas' 
  AND column_name = 'atr';

-- Si NO existe, agregarlo:
ALTER TABLE facturas 
ADD COLUMN IF NOT EXISTS atr VARCHAR(10) DEFAULT '2.0TD';

-- Crear índice para mejorar consultas
CREATE INDEX IF NOT EXISTS idx_facturas_atr ON facturas(atr);

-- ============================================
-- 2. ACTUALIZAR ATR EXISTENTE SEGÚN POTENCIA
-- ============================================

-- Marcar como 3.0TD las facturas con potencia >= 15kW
UPDATE facturas 
SET atr = '3.0TD' 
WHERE potencia_p1_kw >= 15 
  AND (atr IS NULL OR atr = '2.0TD');

-- Asegurar que el resto sean 2.0TD
UPDATE facturas 
SET atr = '2.0TD' 
WHERE potencia_p1_kw < 15 
  AND (atr IS NULL OR atr != '2.0TD');

-- ============================================
-- 3. VERIFICAR CAMPOS P4/P5/P6 (Ya deberían existir)
-- ============================================

-- Verificar estructura de la tabla facturas
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'facturas' 
  AND column_name LIKE '%_p%'
ORDER BY column_name;

-- Si NO existen (poco probable), agregarlos:
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS consumo_p4_kwh DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS consumo_p5_kwh DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS consumo_p6_kwh DOUBLE PRECISION;

ALTER TABLE facturas ADD COLUMN IF NOT EXISTS potencia_p3_kw DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS potencia_p4_kw DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS potencia_p5_kw DOUBLE PRECISION;
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS potencia_p6_kw DOUBLE PRECISION;

-- ============================================
-- 4. CREAR TABLA TARIFAS (si no existe)
-- ============================================

CREATE TABLE IF NOT EXISTS tarifas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    comercializadora VARCHAR(100) NOT NULL,
    atr VARCHAR(10) NOT NULL,  -- '2.0TD' o '3.0TD'
    tipo VARCHAR(50),  -- 'fija', 'indexada', etc.
    
    -- Precios energía (€/kWh)
    energia_p1_eur_kwh DOUBLE PRECISION,
    energia_p2_eur_kwh DOUBLE PRECISION,
    energia_p3_eur_kwh DOUBLE PRECISION,
    energia_p4_eur_kwh DOUBLE PRECISION,
    energia_p5_eur_kwh DOUBLE PRECISION,
    energia_p6_eur_kwh DOUBLE PRECISION,
    
    -- Precios potencia (€/kW·día)
    potencia_p1_eur_kw_dia DOUBLE PRECISION,
    potencia_p2_eur_kw_dia DOUBLE PRECISION,
    potencia_p3_eur_kw_dia DOUBLE PRECISION,
    potencia_p4_eur_kw_dia DOUBLE PRECISION,
    potencia_p5_eur_kw_dia DOUBLE PRECISION,
    potencia_p6_eur_kw_dia DOUBLE PRECISION,
    
    -- Otros campos
    coste_fijo_mes DOUBLE PRECISION,
    permanencia_meses INTEGER,
    penalizacion TEXT,
    fecha_inicio DATE,
    fecha_fin DATE,
    version VARCHAR(50),
    condiciones_json JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_tarifas_atr ON tarifas(atr);
CREATE INDEX IF NOT EXISTS idx_tarifas_comercializadora ON tarifas(comercializadora);

-- ============================================
-- 5. INSERTAR TARIFAS 2.0TD EXISTENTES
-- ============================================

-- Naturgy - Por Uso Luz (24h)
INSERT INTO tarifas (
    nombre, comercializadora, atr, tipo,
    energia_p1_eur_kwh, energia_p2_eur_kwh, energia_p3_eur_kwh,
    potencia_p1_eur_kw_dia, potencia_p2_eur_kw_dia,
    fecha_inicio, version
) VALUES (
    'Tarifa Por Uso Luz', 'Naturgy', '2.0TD', 'fija',
    0.120471, 0.120471, 0.120471,  -- Tarifa plana 24h
    0.111815, 0.033933,
    '2026-01-01', 'naturgy_v1'
) ON CONFLICT DO NOTHING;

-- Naturgy - Noche Luz ECO (3 periodos)
INSERT INTO tarifas (
    nombre, comercializadora, atr, tipo,
    energia_p1_eur_kwh, energia_p2_eur_kwh, energia_p3_eur_kwh,
    potencia_p1_eur_kw_dia, potencia_p2_eur_kw_dia,
    fecha_inicio, version
) VALUES (
    'Tarifa Noche Luz ECO', 'Naturgy', '2.0TD', 'fija',
    0.190465, 0.117512, 0.082673,
    0.111815, 0.033933,
    '2026-01-01', 'naturgy_v1'
) ON CONFLICT DO NOTHING;

-- Iberdrola - Plan Especial plus 15%TE (24h con BOE 2025)
INSERT INTO tarifas (
    nombre, comercializadora, atr, tipo,
    energia_p1_eur_kwh, energia_p2_eur_kwh, energia_p3_eur_kwh,
    potencia_p1_eur_kw_dia, potencia_p2_eur_kw_dia,
    fecha_inicio, version, condiciones_json
) VALUES (
    'Plan Especial plus 15%TE 1p', 'Iberdrola', '2.0TD', 'fija',
    0.127394, 0.127394, 0.127394,  -- Tarifa plana 24h
    0.073777, 0.001911,  -- Peajes + Cargos BOE 2025
    '2026-01-01', 'iberdrola_v1',
    '{"fuente": "imagen_iberdrola.png", "periodos": "1p", "nota": "Precios potencia = peajes regulados BOE 2025"}'::jsonb
) ON CONFLICT DO NOTHING;

-- Endesa - Libre Promo 1er año
INSERT INTO tarifas (
    nombre, comercializadora, atr, tipo,
    energia_p1_eur_kwh, energia_p2_eur_kwh, energia_p3_eur_kwh,
    potencia_p1_eur_kw_dia, potencia_p2_eur_kw_dia,
    permanencia_meses, penalizacion,
    fecha_inicio, fecha_fin, version, condiciones_json
) VALUES (
    'Libre Promo 1er año', 'Endesa', '2.0TD', 'fija',
    0.105900, 0.105900, 0.105900,
    0.090214, 0.090214,
    12, '5% termino energia sin descuento',
    '2026-01-01', '2026-12-31', 'endesa_v1',
    '{"fuente": "pdf_endesa_libre_con_permanencia", "descuento": "10% energia primer año"}'::jsonb
) ON CONFLICT DO NOTHING;

-- Endesa - Libre Base
INSERT INTO tarifas (
    nombre, comercializadora, atr, tipo,
    energia_p1_eur_kwh, energia_p2_eur_kwh, energia_p3_eur_kwh,
    potencia_p1_eur_kw_dia, potencia_p2_eur_kw_dia,
    fecha_inicio, version
) VALUES (
    'Libre Base', 'Endesa', '2.0TD', 'fija',
    0.132375, 0.132375, 0.132375,
    0.090214, 0.090214,
    '2026-01-01', 'endesa_v1'
) ON CONFLICT DO NOTHING;

-- ============================================
-- 6. PLANTILLA PARA TARIFAS 3.0TD (PENDIENTE)
-- ============================================

-- EJEMPLO: Endesa 3.0TD Comercial (6 periodos)
-- NOTA: Estos valores son EJEMPLOS, necesitas obtener los reales del PO

/*
INSERT INTO tarifas (
    nombre, comercializadora, atr, tipo,
    energia_p1_eur_kwh, energia_p2_eur_kwh, energia_p3_eur_kwh,
    energia_p4_eur_kwh, energia_p5_eur_kwh, energia_p6_eur_kwh,
    potencia_p1_eur_kw_dia, potencia_p2_eur_kw_dia, potencia_p3_eur_kw_dia,
    potencia_p4_eur_kw_dia, potencia_p5_eur_kw_dia, potencia_p6_eur_kw_dia,
    fecha_inicio, version
) VALUES (
    'Tarifa 3.0TD Comercial', 'Endesa', '3.0TD', 'fija',
    0.145, 0.130, 0.115, 0.110, 0.105, 0.095,  -- Energía P1-P6
    0.120, 0.110, 0.100, 0.090, 0.080, 0.070,  -- Potencia P1-P6
    '2026-01-01', 'endesa_3.0TD_v1'
);
*/

-- ============================================
-- 7. CONSULTAS DE VERIFICACIÓN
-- ============================================

-- Ver todas las tarifas por ATR
SELECT atr, comercializadora, nombre, 
       energia_p1_eur_kwh, potencia_p1_eur_kw_dia
FROM tarifas
ORDER BY atr, comercializadora;

-- Contar facturas por ATR
SELECT atr, COUNT(*) as total
FROM facturas
GROUP BY atr;

-- Ver facturas 3.0TD (potencia >= 15kW)
SELECT id, cups, potencia_p1_kw, atr,
       consumo_p1_kwh, consumo_p4_kwh  -- P4 solo existe en 3.0TD
FROM facturas
WHERE potencia_p1_kw >= 15
LIMIT 10;

-- ============================================
-- 8. ROLLBACK (si algo sale mal)
-- ============================================

-- Eliminar campo ATR
-- ALTER TABLE facturas DROP COLUMN IF EXISTS atr;

-- Eliminar índice
-- DROP INDEX IF EXISTS idx_facturas_atr;

-- Vaciar tabla tarifas
-- TRUNCATE TABLE tarifas;
