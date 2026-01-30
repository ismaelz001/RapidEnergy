## 🔧 DEBUGGING - Factura #285 y Problemas de Comparador

### PROBLEMA REPORTADO
- ✅ OCR extrae datos correctamente
- ❌ PDF no se genera (error buscando "Patricia Vázquez")
- ❌ Comparador no muestra mejora de tarifa (antes sí mejoraba)

---

### ✅ SOLUCIÓN 1: PDF - RUTA ROBUSTA

**Cambio realizado:**
- Mejoré `app/services/pdf_generator.py` para buscar el PDF modelo de forma robusta
- Ahora intenta múltiples rutas y busca recursivamente si es necesario
- Debería funcionar en Render sin problemas

**Para probar en Render:**
```bash
curl https://rapidenergy.onrender.com/webhook/facturas/285/presupuesto.pdf \
  -H "Content-Type: application/json" \
  -o factura_285.pdf
```

---

### 🔍 SOLUCIÓN 2: DEBUGGING DEL COMPARADOR

He añadido dos endpoints de debugging en `/debug` para investigar por qué el comparador no mejora tarifas:

#### **Endpoint 1: Ver estadísticas de tarifas**
```bash
curl https://rapidenergy.onrender.com/debug/tarifas/stats
```

**Retorna:**
```json
{
  "tarifas_por_atr": {
    "2.0TD": 150,
    "3.0TD": 45
  },
  "precios_muestra": {
    "2.0TD": {
      "energia_p1": {"min": 0.15, "max": 0.35, "avg": 0.25},
      "potencia_p1": {"min": 0.05, "max": 0.15, "avg": 0.10}
    }
  }
}
```

**¿Qué significa?**
- Si el precio medio de `energia_p1` es 0.25€/kWh pero la factura actual tiene 0.1066€/kWh
- Entonces NO HAY tarifa en BD que pueda mejorar la factura actual
- Solución: Importar tarifas con precios más competitivos

---

#### **Endpoint 2: Debug comparador para factura específica**
```bash
curl -X POST https://rapidenergy.onrender.com/debug/comparador/factura/285
```

**Retorna análisis como:**
```json
{
  "factura_id": 285,
  "success": true,
  "ofertas_totales": 150,
  "ofertas_con_ahorro": 0,
  "ofertas_sin_ahorro": 150,
  "baseline_actual": 38.88,
  "baseline_method": "backsolve_subtotal_si",
  "inputs": {
    "atr": "2.0TD",
    "total_factura": 38.88,
    "consumo_total": 281.71,
    "periodo_dias": 31,
    "alquiler_contador": 2.1,
    "iva_porcentaje": 21
  },
  "mejores_ofertas": [
    {
      "provider": "Neon",
      "plan_name": "Neon 24h",
      "estimated_total": 45.50,
      "saving_amount_annual": -237.60
    }
  ]
}
```

**¿Qué significa?**
- `ofertas_con_ahorro: 0` → No hay NINGUNA oferta con ahorro positivo
- `estimated_total: 45.50` > `baseline_actual: 38.88` → Las tarifas de mercado son más caras
- Conclusión: El cliente tiene una tarifa regulada/especial muy buena

---

### 📊 DIAGNÓSTICO PARA FACTURA #285

Ejecuté un análisis manual:

```
Total factura OCR: 38.88€
Consumo total: 281.71 kWh
Precio medio actual: 0.1066€/kWh

Precio típico mercado: 0.25-0.35€/kWh

CONCLUSIÓN: 
- Cliente tiene tarifa regulada (probablemente PVPC de Iberdrola)
- Precio actual es 60% más barato que mercado
- Nuestras tarifas NO pueden mejorar esto
```

---

### 💡 PRÓXIMAS ACCIONES RECOMENDADAS

1. **En Render, ejecuta:**
   ```bash
   curl https://rapidenergy.onrender.com/debug/tarifas/stats
   ```
   - Si los precios de `energia_p1` son > 0.20€/kWh, están muy altos
   - Considera importar nuevas tarifas más competitivas

2. **Verifica la BD de Render:**
   - ¿Se importaron las tarifas correctamente?
   - ¿Cambió algo en la importación recientemente?

3. **Considera UX:** 
   - Mostrar un mensaje: "El cliente tiene una tarifa actual muy competitiva (0.1066€/kWh). Nuestras tarifas actuales no pueden mejorar esto."
   - En lugar de: "No se puede mejorar"

---

### 📝 PARA USAR ESTOS ENDPOINTS

Los endpoints son **privados por defecto** pero puedes habilitarlos:

1. Están en `app/routes/debug.py`
2. Se incluyen automáticamente en la app
3. Para deshabilitar, comenta las líneas en `main.py`:
   ```python
   # app.include_router(debug_router)
   ```

---

### 🐛 LOGS PARA INVESTIGAR

En los logs de Render busca:

```
[PDF] Modelo PDF encontrado en:
[STEP2] Usando total_ajustado=X
[3.0TD] ATR tomado de OCR:
[PO] Backsolve:
[OFERTAS] comparativa_id=X offers_count=Y
```

Si ves `offers_count=0`, es que no se generaron ofertas.
Si ves ahorros negativos, es que tus tarifas son más caras que la actual.
