# PDF Formula Breakdown Implementation - Audit Trail

## ✅ Implementación Completada

Se ha añadido una nueva **Tabla C: Cálculo paso a paso** al PDF de presupuesto que muestra el desglose exacto de la fórmula de cálculo, tal como solicitó el usuario en sus notas manuscritas.

## 📋 Estructura de la Tabla (Tabla C)

La tabla ahora muestra los siguientes pasos en orden:

| PASO | CONCEPTO | FÓRMULA / CÁLCULO | IMPORTE (€) |
|------|----------|------|---------|
| 1 | POTENCIA (P1+P2) | (P1_kW + P2_kW) × días × tarifa | {coste_p} |
| 2 | CONSUMO (P1+P2+P3) | (P1_kWh + P2_kWh + P3_kWh) × tarifa | {coste_e} |
|   | Total Potencia + Consumo |   | {subtotal_ep} |
| 3 | + Bono Social (si aplica) | Descuento regulatorio | -{bono_social} |
|   | **═══ TOTAL 1 ═══** | Subtotal (antes de impuestos) | {total_1} |
| 4 | × Impuesto Eléctrico (IEE) | Subtotal × 5.1127% | {iee_amount} |
|   | **═══ TOTAL 2 ═══** | Después de impuesto eléctrico | {total_2} |
| 5 | + Alquiler Contador | Cuota fija de alquiler | {alquiler} |
|   | **═══ TOTAL 3 ═══** | Antes de IVA | {total_3} |
| 6 | IVA (21%) | Total 3 × 21% | {iva_amount} |
|   | **═══ IMPORTE TOTAL ═══** | TOTAL CON IVA | {total_est} |

## 🎯 Beneficios para Auditoría

1. **Transparencia Total**: Cada línea de la factura se puede verificar manualmente
2. **Desglose Estructurado**: Los pasos siguen el orden exacto de cálculo regulatorio
3. **Fácil Localización de Errores**: Si hay discrepancias, se pueden identificar inmediatamente
4. **Validación de Comercializadora**: Se pueden comparar los cálculos con lo que factura el proveedor actual

## 📝 Cambios de Código

**Archivo**: `app/services/pdf_generator.py`

### Líneas modificadas: 264-329

Se reemplazó la tabla C simple por una tabla completa que:
- Extrae datos reales de potencia/consumo de la factura
- Calcula cada paso del proceso según regulación española
- Aplica correctamente IEE (5.1127%) y Bono Social
- Desglosalquileres y servicios adicionales
- Muestra el IVA (21%) final

### Validaciones implementadas:
✅ Constante IEE: 0.0511269632 (5.1127%)
✅ Cálculo de potencia: (P1 + P2) × kW × días × tarifa
✅ Cálculo de consumo: (P1 + P2 + P3) × kWh × tarifa
✅ Bono Social: Aplicado si existe en breakdown
✅ IVA: 21% sobre subtotal después de impuestos
✅ Alquiler contador: Incluido como línea separada

## 🔄 Commit

```
commit 606cc14
Author: Test Agent
Date: [timestamp]

FEAT: Add step-by-step formula breakdown in PDF for audit trail

- Added Table C showing complete calculation breakdown
- Each step (Potencia, Consumo, IEE, IVA) separately displayed
- Enables immediate error detection during audit
- Matches user specification exactly
```

## ✨ Resultado Final

Los usuarios ahora pueden:
1. **Abrir el PDF generado** después de subir una factura
2. **Ver la Tabla C** con el desglose completo
3. **Comparar línea por línea** con la factura actual
4. **Identificar inmediatamente** si hay errores en el cálculo de la nueva tarifa

**Estado**: ✅ Implementado y desplegado en producción (Render auto-deploy)

---

**Fecha de implementación**: 2025-01-26
**Usuario**: Solicitud de auditoría con notas manuscritas
**Sprint**: S5 - QA & Audit Trail
