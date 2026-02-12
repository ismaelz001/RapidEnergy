# 🔐 CREDENCIALES DE PRUEBA - Sistema CRM

**Fecha:** 10 de febrero de 2026  
**Entorno:** Producción (Vercel + Render + Neon)

---

## 📋 USUARIOS DE PRUEBA

### 👨‍💻 ROL: DEV (Acceso Total)

```
Email:    ismael@rodorte.com
Password: dev2026!
Role:     dev
User ID:  1
```

**Permisos:**
- ✅ Ve TODOS los casos, clientes, comisiones
- ✅ Acceso completo al panel de gestión
- ✅ Puede crear/editar/eliminar todo sin restricciones
- ✅ Puede gestionar pagos de comisiones

---

### 👔 ROL: CEO (Gestión Empresarial)

#### CEO 1 - José Moreno (Asesoría Energética)
```
Email:      jose@asesoria.com
Password:   ceo2026!
Role:       ceo
User ID:    2
Company ID: 1 (Asesoría Energética)
```

**Comerciales a su cargo:**
- Ana López (ID: 3)
- Carlos Ruiz (ID: 4)
- Juan Pérez (ID: 5)

#### CEO 2 - Laura Martínez (EnergyPlus)
```
Email:      laura@energyplus.com
Password:   ceo2026!
Role:       ceo
User ID:    6
Company ID: 2 (EnergyPlus)
```

**Comerciales a su cargo:**
- Pedro García (ID: 7)
- Sofia Torres (ID: 8)

#### CEO 3 - David Sánchez (PowerCo)
```
Email:      david@powerco.com
Password:   ceo2026!
Role:       ceo
User ID:    9
Company ID: 3 (PowerCo)
```

**Comerciales a su cargo:**
- Miguel Ángel (ID: 10)
- Elena Rodríguez (ID: 11)

**Permisos CEO:**
- ✅ Acceso al panel de gestión CRM
- ✅ Ve casos y clientes de SU EMPRESA únicamente
- ✅ Ve comisiones de sus comerciales
- ✅ Puede validar y pagar comisiones
- ✅ Puede crear casos manuales
- ❌ NO ve datos de otras empresas

---

### 🤝 ROL: COMERCIAL/ASESOR (Solo Comparador)

#### COMPANY 1: Asesoría Energética (José Moreno)

**Comercial 1 - Ana López**
```
Email:      ana@asesoria.com
Password:   comercial2026!
Role:       comercial
User ID:    3
Company ID: 1
Manager:    José Moreno (CEO, ID=2)
```

**Comercial 2 - Carlos Ruiz**
```
Email:      carlos@asesoria.com
Password:   comercial2026!
Role:       comercial
User ID:    4
Company ID: 1
Manager:    José Moreno (CEO, ID=2)
```

**Comercial 3 - Juan Pérez**
```
Email:      juan@test.com
Password:   comercial2026!
Role:       comercial
User ID:    5
Company ID: 1
Manager:    José Moreno (CEO, ID=2)
```

#### COMPANY 2: EnergyPlus (Laura Martínez)

**Comercial 4 - Pedro García**
```
Email:      pedro@energyplus.com
Password:   comercial2026!
Role:       comercial
User ID:    7
Company ID: 2
Manager:    Laura Martínez (CEO, ID=6)
```

**Comercial 5 - Sofia Torres**
```
Email:      sofia@energyplus.com
Password:   comercial2026!
Role:       comercial
User ID:    8
Company ID: 2
Manager:    Laura Martínez (CEO, ID=6)
```

#### COMPANY 3: PowerCo (David Sánchez)

**Comercial 6 - Miguel Ángel**
```
Email:      miguel@powerco.com
Password:   comercial2026!
Role:       comercial
User ID:    10
Company ID: 3
Manager:    David Sánchez (CEO, ID=9)
```

**Comercial 7 - Elena Rodríguez**
```
Email:      elena@powerco.com
Password:   comercial2026!
Role:       comercial
User ID:    11
Company ID: 3
Manager:    David Sánchez (CEO, ID=9)
```

**Permisos COMERCIAL:**
- ✅ Acceso al comparador de facturas
- ✅ Ve SOLO sus propios clientes y casos
- ✅ Puede crear casos asignados a sí mismo
- ❌ NO accede al panel de gestión (`/gestion`)
- ❌ NO puede ver comisiones
- ❌ NO puede cambiar estado a "activo"

---

## 🚀 CÓMO USAR EN PRODUCCIÓN

### Opción 1: Consola del Navegador (Desarrollo/Testing)

Abre la consola del navegador (`F12`) y ejecuta:

```javascript
// Como DEV (acceso total)
localStorage.setItem('user_role', 'dev');
localStorage.setItem('user_id', '1');
location.reload();

// Como CEO (gestión empresarial)
localStorage.setItem('user_role', 'ceo');
localStorage.setItem('user_id', '2');
location.reload();

// Como COMERCIAL (solo comparador)
localStorage.setItem('user_role', 'comercial');
localStorage.setItem('user_id', '3');  // Ana, Carlos (4), o Juan (5)
location.reload();
```

### Opción 2: URL con Parámetros (Futuro)

```
https://tu-dominio.vercel.app/?test_user=dev
https://tu-dominio.vercel.app/?test_user=ceo
https://tu-dominio.vercel.app/?test_user=comercial
```

---

## 🔍 VERIFICAR PERMISOS ACTIVOS

Ejecuta en consola del navegador:

```javascript
console.log({
  user_id: localStorage.getItem('user_id'),
  user_role: localStorage.getItem('user_role')
});
```

---

## 📊 MATRIZ DE ACCESO POR ROL

| Funcionalidad | DEV | CEO | COMERCIAL |
|--------------|-----|-----|-----------|
| Ver todos los casos | ✅ | ❌ (solo su empresa) | ❌ (solo suyos) |
| Ver todos los clientes | ✅ | ❌ (solo su empresa) | ❌ (solo suyos) |
| Crear caso manual | ✅ | ✅ | ✅ (solo a sí mismo) |
| Editar datos caso | ✅ | ✅ | ✅ (solo propios) |
| Cambiar estado hasta `firmado` | ✅ | ✅ | ✅ |
| Cambiar estado a `activo` | ✅ | ✅ | ❌ |
| Crear comisión manual | ✅ | ✅ | ❌ |
| Validar comisión | ✅ | ✅ | ❌ |
| Pagar comisión | ✅ | ✅ | ❌ |
| Ver todas las comisiones | ✅ | ✅ (su empresa) | ❌ |
| Acceso a `/gestion` | ✅ | ✅ | ❌ |
| Acceso comparador | ✅ | ✅ | ✅ |

---

## 🔄 FLUJO DE DATOS POR ROL

### DEV (sin filtros)
```sql
SELECT * FROM casos;
SELECT * FROM clientes;
SELECT * FROM comisiones_generadas;
```

### CEO (filtro por company_id)
```sql
SELECT * FROM casos WHERE company_id = 1;
SELECT * FROM clientes WHERE company_id = 1;
SELECT * FROM comisiones_generadas WHERE company_id = 1;
```

### COMERCIAL (filtro por asesor_id/comercial_id)
```sql
SELECT * FROM casos WHERE asesor_user_id = 3;
SELECT * FROM clientes WHERE comercial_id = 3;
-- NO accede a comisiones
```

---

## ⚠️ NOTAS IMPORTANTES

1. **Sistema Mock**: Este es un sistema de autenticación temporal para desarrollo
2. **No usar en producción final**: Implementar JWT/OAuth antes del lanzamiento
3. **Headers enviados**: Todos los requests incluyen `X-User-Id` en el header
4. **Base de datos**: Los datos de usuarios están en tabla `users` de Neon
5. **Sincronización**: Los IDs deben coincidir con los registros reales en DB

---

## 🛠️ TROUBLESHOOTING

### "No veo mis datos"
```javascript
// Verifica que el user_id existe en la base de datos
// Verifica que el role es correcto
console.log('User ID:', localStorage.getItem('user_id'));
console.log('Role:', localStorage.getItem('user_role'));
```

### "Acceso denegado"
- Verifica que el rol permite acceder a esa ruta
- Comerciales NO pueden acceder a `/gestion`

### "No se filtran los datos"
- Verifica que `company_id` esté configurado en el usuario
- CEO necesita `company_id` válido para ver datos

---

## 📝 CHANGELOG

- **10/02/2026**: Creación inicial del sistema de credenciales
- Sistema de autenticación mock implementado
- Filtros por rol en backend activos
- Headers `X-User-Id` enviados desde frontend

---

## 🔒 SEGURIDAD

**⚠️ RECORDATORIO**: Estas credenciales son **SOLO PARA DESARROLLO/TESTING**

En producción real:
1. Implementar JWT con expiración
2. Usar OAuth 2.0 / OpenID Connect
3. Cifrar contraseñas con bcrypt
4. Rate limiting en endpoints
5. Logging de accesos
6. 2FA para roles CEO/DEV
