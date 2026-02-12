-- Script para insertar usuarios y companies de prueba en Neon PostgreSQL
-- Ejecutar en la consola SQL de Neon: https://console.neon.tech/

-- 1. Insertar Companies
INSERT INTO companies (id, nombre, email, telefono, activo, created_at) 
VALUES 
  (1, 'Asesoría Energética', 'info@asesoria.com', '912345678', true, NOW()),
  (2, 'EnergyPlus', 'info@energyplus.com', '913456789', true, NOW()),
  (3, 'PowerCo', 'info@powerco.com', '914567890', true, NOW())
ON CONFLICT (id) DO UPDATE 
SET nombre = EXCLUDED.nombre, 
    email = EXCLUDED.email;

-- 2. Insertar Usuarios
INSERT INTO users (id, name, email, role, is_active, company_id, created_at) 
VALUES 
  -- DEV
  (1, 'Ismael Rodríguez', 'ismael@rodorte.com', 'dev', true, NULL, NOW()),
  
  -- CEOs
  (2, 'José Moreno', 'jose@asesoria.com', 'ceo', true, 1, NOW()),
  (6, 'Laura Martínez', 'laura@energyplus.com', 'ceo', true, 2, NOW()),
  (9, 'David Sánchez', 'david@powerco.com', 'ceo', true, 3, NOW()),
  
  -- COMERCIALES - Company 1
  (3, 'Ana López', 'ana@asesoria.com', 'comercial', true, 1, NOW()),
  (4, 'Carlos Ruiz', 'carlos@asesoria.com', 'comercial', true, 1, NOW()),
  (5, 'Juan Pérez', 'juan@test.com', 'comercial', true, 1, NOW()),
  
  -- COMERCIALES - Company 2
  (7, 'Pedro García', 'pedro@energyplus.com', 'comercial', true, 2, NOW()),
  (8, 'Sofia Torres', 'sofia@energyplus.com', 'comercial', true, 2, NOW()),
  
  -- COMERCIALES - Company 3
  (10, 'Miguel Ángel', 'miguel@powerco.com', 'comercial', true, 3, NOW()),
  (11, 'Elena Rodríguez', 'elena@powerco.com', 'comercial', true, 3, NOW())
ON CONFLICT (id) DO UPDATE 
SET name = EXCLUDED.name,
    email = EXCLUDED.email,
    role = EXCLUDED.role,
    company_id = EXCLUDED.company_id;

-- 3. Actualizar secuencias para que los próximos IDs sean correctos
SELECT setval('companies_id_seq', (SELECT MAX(id) FROM companies));
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));

-- 4. Verificar inserciones
SELECT id, name, email, role, company_id FROM users ORDER BY id;
SELECT id, nombre FROM companies ORDER BY id;
