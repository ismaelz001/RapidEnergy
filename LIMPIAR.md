# 🧹 Checklist: Archivos a Eliminar Después del Testing

Este archivo ayuda a mantener limpia la repo después de los tests.

## ✅ Archivos de Testing (Eliminar después de validar)

```bash
# Eliminar cuando todo funcione y subas a producción:

rm -f test.py                 # Script simple de test
rm -f test_ocr_directo.py     # Test directo
rm -f test_ocr_upload.py      # Test del endpoint
rm -f analizar_facturas.py    # Script de análisis

# En Windows (PowerShell):
Remove-Item test.py, test_ocr_directo.py, test_ocr_upload.py, analizar_facturas.py
```

## ✅ Documentación de Testing (Eliminar cuando no la necesites)

```bash
# Si todo funciona, puedes eliminar:

rm -f TEST.md                 # Instrucciones de testing
rm -f TESTING_LOCAL.txt       # Este archivo de resumen
rm -f LIMPIAR.md              # Este checklist
```

## ✅ Cuando Eliminar

### Opción A: Mantener tests durante desarrollo
**Mantén**: `test.py`, `TEST.md`
**Elimina**: Lo demás

### Opción B: Repo completamente limpia para producción
**Elimina**: Todo

### Opción C: Mantener para CI/CD (Recomendado)
**Mantén**: 
- `test.py` (para CI/CD pipelines)
- `TEST.md` (documentación)

**Elimina**:
- `test_ocr_directo.py`
- `test_ocr_upload.py`
- `analizar_facturas.py`
- `TESTING_LOCAL.txt`
- `LIMPIAR.md`

## 🎯 Recomendación Final

**Lo mejor es mantener:**
- ✅ `test.py` - Para testing rápido/CI
- ✅ `TEST.md` - Documentación

**Y eliminar:**
- ❌ Todo lo demás

Así la repo está limpia pero puedes testear en cualquier momento.

## 📋 Checklist de Producción

Antes de subir a producción:

- [ ] ¿Ejecuté `python test.py`?
- [ ] ¿Pasaron todos los tests?
- [ ] ¿Validé con múltiples facturas (Iberdrola, Naturgy, etc.)?
- [ ] ¿Eliminé archivos innecesarios de testing?
- [ ] ¿El repo está limpio?

```bash
# Comando para ver qué se va a subir:
git status

# Comando para ver si hay archivos de test:
ls -la test*.py
```

## ✨ Después de Subir a Producción

Una vez que todo está funcionando en Render/Vercel/Neon:

```bash
# Opción 1: Mantener test.py para debugging futuro
# (No hacer nada, ya está en .gitignore o puedes dejar)

# Opción 2: Limpiar completamente
git rm test.py TEST.md TESTING_LOCAL.txt LIMPIAR.md
git commit -m "Remove testing files"
git push
```

---

**¡Listo! Cuando termines el testing, usa este checklist para limpiar.**
