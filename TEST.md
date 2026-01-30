# 🧪 Testing OCR Local

## ⚡ Requisitos

Para testear el OCR localmente necesitas:
- Python 3.9+ instalado
- Dependencias: `pip install -r requirements.txt`

## 🚀 Ejecutar Tests

### Test 1: OCR Directo (Recomendado)
```bash
python test_ocr_directo.py
```
- **Sin servidor**: Ejecuta rápido
- **Valida**: Qué campos extrae el OCR
- **Tiempo**: 30 segundos

### Test 2: Endpoint HTTP
```bash
# Terminal 1: Iniciar servidor
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Ejecutar test
python test_ocr_upload.py
```
- **Con servidor**: Test completo del endpoint
- **Valida**: Flujo completo de upload
- **Tiempo**: 1 minuto

### Test 3: Análisis Estático (Debug)
```bash
python analizar_facturas.py
```
- **Sin servidor**: Analiza PDFs crudos
- **Útil para**: Debuggear qué está en los PDFs vs qué extrae OCR
- **Tiempo**: 20 segundos

## 📊 Qué se valida

Campos críticos:
- ✅ CUPS (código suministro)
- ✅ Total factura
- ✅ Consumo P1, P2, P3
- ✅ Potencia P1, P2
- ✅ Período en días
- ✅ Fecha

Validaciones automáticas:
- ✅ Sin valores negativos
- ✅ Sin valores absurdos
- ✅ Formato correcto

## ✅ Resultado Esperado

```
════════════════════════════════════════════════════════════════
✅ CAMPOS EXTRAÍDOS: 9/9
❌ PROBLEMAS: 0/9
════════════════════════════════════════════════════════════════

🎉 OCR FUNCIONA CORRECTAMENTE
```

## ⚠️ Si hay errores

1. Verifica dependencias:
```bash
pip install -r requirements.txt
```

2. Si campos faltan, ejecuta análisis:
```bash
python analizar_facturas.py
```

3. Compara datos reales vs extraídos

4. Edita `app/services/ocr.py` si necesitas ajustar regex

5. Vuelve a testear

## 🎯 Próximos pasos

✅ Una vez que los tests pasen localmente:
1. Verifica con varias facturas (Iberdrola, Naturgy, etc.)
2. Sube a Render/Vercel/Neon
3. Testea en producción
