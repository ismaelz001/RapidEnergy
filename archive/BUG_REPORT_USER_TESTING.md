# 🐛 BUG REPORT - Testing Manual Usuario

## Fecha: 2026-01-12 09:24
## Tester: Usuario (Testing Real)

---

## ✅ LO QUE FUNCIONA

| Feature | Estado | Detalle |
|---------|--------|---------|
| Panel Facturas - CUPS | ✅ OK | Se guarda correctamente |
| Panel Clientes - Editar nombre | ✅ OK | Se persiste bien |
| Panel Clientes - Edición manual | ✅ OK | Cambios se guardan |
| Enlace Cliente-Factura | ✅ OK | Nombre aparece en panel facturas |

---

## ❌ BUGS CRÍTICOS ENCONTRADOS

### BUG 7: OCR Confunde CUPS con Nombre Cliente 🔴 P0
**Severidad:** CRÍTICA
**Descripción:** Al cargar factura, OCR extrae CUPS y lo asigna al campo nombre del cliente
**Ejemplo:**
```
CUPS real: ES0031103378680001TE
Titular real: JOSE ANTONIO RODRIGUEZ

OCR extrae:
- cups: "ESVEROCANJEARTUSALDOHACIEN" (WRONG)
- titular/cliente.nombre: "ES0031103378680001TE" (WRONG - es el CUPS!)
```

**Impacto:** Cliente creado con nombre = CUPS → datos inútiles
**Causa probable:** Regex OCR captura CUPS y lo asigna a campo incorrecto
**Fix requerido:**
- Mejorar `app/services/ocr.py` extracción titular
- Validar que titular NO tenga formato ES + números
- Separar claramente extracción CUPS vs titular

---

### BUG 8: Comparador Falla / Resultados Inútiles 🔴 P0
**Severidad:** CRÍTICA
**Descripción:** Al ejecutar comparación, resultados son inútiles/incorrectos
**Pasos:**
1. Usuario copia CUPS y nombre manualmente
2. Click "Comparar"
3. Resultado: falla o muestra datos sin sentido

**Posibles causas:**
- OCR extrae consumos incorrectos (lecturas vs periodo)
- Total factura incorrecto
- Periodo_dias NULL → error P1
- Combinación de bugs OCR anteriores

**Fix requerido:**
- Depende de fixes OCR (BUG 1-4, 7)
- Verificar que comparador reciba datos válidos

---

### BUG 9: Falta Botón "Eliminar Factura" 🟡 P1
**Severidad:** ALTA
**Descripción:** Panel facturas no tiene opción para eliminar facturas
**Lógica requerida:**

```javascript
if (factura.tiene_errores_criticos) {
  // Sin CUPS válido, sin cliente, datos incompletos
  → Permitir eliminar SIN confirmación
} else if (factura.cliente_id && cliente.tiene_mas_facturas) {
  → Permitir eliminar CON confirmación
  → Modal: "Esta factura está enlazada al cliente X. ¿Seguro?"
} else if (factura.cliente_id && cliente.solo_tiene_esta_factura) {
  → BLOQUEAR eliminación
  → Error: "No puedes eliminar la única factura del cliente. Elimina el cliente primero."
}
```

**Fix requerido:**
- Añadir botón "Eliminar" en panel facturas
- Implementar lógica de restricciones
- Modal de confirmación
- Endpoint DELETE en backend

---

## 📊 PRIORIDADES

### 🔴 P0 - BLOQUEANTES (Hacer YA)
1. **BUG 7** - OCR CUPS/Titular confundidos
2. **BUG 8** - Comparador inútil (depende de OCR)

### 🟡 P1 - ALTO (Próxima sesión)
3. **BUG 9** - Eliminar factura
4. **BUG 1-4** - Refinamiento OCR general

### 🟢 P2 - MEDIO
5. Validaciones adicionales
6. Mejoras UX

---

## 🎯 PLAN DE ACCIÓN INMEDIATO

### Fix 1: OCR - Separar CUPS de Titular
**Archivo:** `app/services/ocr.py`
**Acción:**
```python
# Validación adicional después de extracción
if titular and re.match(r'^ES\d{16,20}', titular):
    # Titular tiene formato de CUPS → ERROR
    titular = None  # Resetear
    
if cups and not re.match(r'^ES\d{16,20}', cups):
    # CUPS no tiene formato correcto
    cups = None
```

### Fix 2: Validación Pre-Comparación
**Archivo:** `app/services/comparador.py`
**Acción:**
```python
# Verificar datos mínimos antes de comparar
if not factura.cups or not re.match(r'^ES\d{16,20}', factura.cups):
    raise DomainError("CUPS_INVALID", "CUPS no válido")

if factura.consumo_p1_kwh > 10000:  # Sospechoso
    raise DomainError("CONSUMPTION_SUSPICIOUS", "Consumo sospechosamente alto - verificar si es lectura")
```

### Fix 3: Botón Eliminar Factura
**Archivo:** `app/facturas/page.jsx`
**Backend:** `app/routes/webhook.py` - Añadir DELETE endpoint
**Acción:**
1. Añadir botón eliminar con icono 🗑️
2. Verificar lógica restricciones
3. Modal confirmación
4. Endpoint DELETE /webhook/facturas/{id}

---

## 🧪 TESTS A REALIZAR (Antes de deploy)

### Pre-commit Checklist
- [ ] Subir factura Iberdrola
- [ ] Verificar CUPS extraído correctamente
- [ ] Verificar titular extraído (no confundido con CUPS)
- [ ] Verificar consumos (no lecturas)
- [ ] Comparar factura
- [ ] Verificar resultados coherentes
- [ ] Editar cliente manualmente
- [ ] Verificar cambios persisten
- [ ] Intentar eliminar factura válida
- [ ] Verificar restricción funciona

---

## 💡 LECCIÓN APRENDIDA

**Testing Manual > Testing Automático para UX**

El usuario detectó en 5 minutos bugs que tests automáticos no capturarían:
- Confusión de campos (CUPS ↔ Titular)
- Resultados "inútiles" del comparador
- Flujos de eliminación faltantes

**Acción futura:** 
- Hacer testing exploratorio después de cada feature
- Usar facturas REALES, no mocks
- Probar flujos completos, no solo endpoints aislados

---

**Estado:** 🔴 BUGS CRÍTICOS DETECTADOS
**Requiere:** Session de fixes OCR + Eliminar factura
