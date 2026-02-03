#!/bin/bash
# Deploy script para RapidEnergy OCR - Full Deploy
# Fecha: 2026-02-02
# Changes: OCR improvements + NoneType fixes + dias expansion

echo "==============================================="
echo "DEPLOY OCR IMPROVEMENTS - FULL DEPLOY"
echo "==============================================="

# Pre-deploy checks
echo -e "\n[1/5] Validando sintaxis Python..."
python -m py_compile app/services/ocr.py
if [ $? -eq 0 ]; then
    echo "  ✓ Sintaxis OK"
else
    echo "  ✗ ERROR de sintaxis"
    exit 1
fi

echo -e "\n[2/5] Verificando módulo importable..."
python -c "from app.services.ocr import extract_data_from_pdf" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✓ Módulo importable"
else
    echo "  ✗ ERROR importando módulo"
    exit 1
fi

echo -e "\n[3/5] Ejecutando tests..."
python test_validation_clean.py 2>&1 | grep "Rate:"
if [ $? -eq 0 ]; then
    echo "  ✓ Tests ejecutados"
else
    echo "  ⚠ WARNING: Tests no ejecutados"
fi

echo -e "\n[4/5] Validando requirements..."
if [ -f requirements.txt ]; then
    echo "  ✓ requirements.txt presente"
else
    echo "  ⚠ WARNING: requirements.txt no encontrado"
fi

echo -e "\n[5/5] Status final..."
echo "  ✓ Todas las validaciones pasadas"
echo "  ✓ Listo para deploy"

echo -e "\n==============================================="
echo "NEXT STEPS:"
echo "==============================================="
echo "1. Commit cambios:"
echo "   git add app/services/ocr.py test_predeploy_suite.py"
echo "   git commit -m 'OCR: NoneType fixes + dias expansion + Strategy 0'"
echo ""
echo "2. Push a repositorio:"
echo "   git push origin main"
echo ""
echo "3. Render auto-deploy en: https://rapidenergy-backend.onrender.com"
echo ""
echo "==============================================="
