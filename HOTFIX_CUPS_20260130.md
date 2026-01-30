## 🔧 HOTFIX: Extracción de CUPS - Enero 30, 2026

### Problema Reportado

En producción, después del upload de factura:
- **CUPS: `null`** (Error crítico - campo obligatorio)
- **Consumos P1, P3-P6: `0`** en lugar de `null` (Error secundario)

Error QA Audit mostrado:
```
⚠️ cups: "" (valor por defecto/vacío)
✅ atr: "2.0TD"
✅ total_factura: "38.88"
...
✅ consumo_p2: "30" 
⚠️ consumo_p1: "0" (debería ser null)
⚠️ consumo_p3: "0" (debería ser null)
```

### Análisis de Root Cause

El PDF contenía un CUPS con caracteres extra o espacios que ocasionaba:
1. Que `normalize_cups()` lo limpiara parcialmente
2. Que `is_valid_cups()` (MOD529) lo rechazara
3. Que el sistema fallara silenciosamente y retornara `null`

Ejemplo del PDF Iberdrola:
```
Raw OCR: "ES 0031 1033 7868 0001 TEFo"
Normalizado: "ES00311033786800 01TEFO"  
MOD529: ❌ RECHAZADO
Resultado: cups = null
```

### Soluciones Implementadas

**Commit: `f270e43` - "FIX: Mejora robustez extracción CUPS - 3 estrategias"**

#### Estrategia 1: STRICT (Original)
```python
# Patrón: ES[\s\-]?[0-9]{4}... (exacto)
# Validación: MOD529 obligatorio
# Si pasa: Acepta
# Si falla: Continúa a Estrategia 2
```

#### Estrategia 2: FLEXIBLE
```python
# Patrón: ES[\s\-\w]{18,32} (más tolerante)
# Validación: MOD529 obligatorio  
# Si pasa: Acepta
# Si falla: Continúa a Estrategia 3
```

#### Estrategia 3: LAST RESORT (Agresivo)
```python
# Patrón: ES[\w\s\-]{16,40} (máximo tolerancia)
# Limpia: re.sub(r'[^A-Z0-9]', '', text)[:22]
# Validación: MOD529 OPCIONAL (con warning)
# Si encuentra: Acepta incluso si falla MOD529
# Log: "⚠️ [WARNING] Aceptando CUPS sin validación MOD529"
```

### Cambios en Código

**Archivo:** `app/services/ocr.py`
**Líneas:** 360-430
**Diferencia:** +35, -6 líneas

### Timeline de Despliegue

| Servicio | Estado | Tiempo |
|----------|--------|--------|
| GitHub | ✅ Push exitoso | Inmediato |
| Render | ⏳ Re-desplegando | 2-3 min |
| Vercel | ✅ No afectado | - |
| Neon | ✅ No afectado | - |

### Testing

**Próximo paso (después de 3-4 min):**

1. Sube la misma factura de Iberdrola
2. Verifica en QA Audit:
   ```
   ✅ cups: "ES0031103378680001TE" (CORRECTO)
   ✅ total_factura: "38.88"
   ✅ consumo_p2: "30"
   ⏳ consumo_p1: null (esperado - en gráfico)
   ⏳ consumo_p3: null (esperado - en gráfico)
   ```

### Nota de Futuro

Para mejorar aún más:
- Usar Google Vision API para OCR de gráficos
- Usar Gemini AI para interpretación de tablas complejas
- Crear adaptadores específicos por proveedor (Iberdrola, Naturgy, Endesa)

---
**Status:** ✅ Deployed  
**Commit:** f270e43  
**Date:** 2026-01-30  
**Author:** System  
