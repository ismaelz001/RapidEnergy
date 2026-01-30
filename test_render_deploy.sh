#!/bin/bash
# Script para testear los endpoints en Render después del deploy

RENDER_URL="https://rapidenergy.onrender.com"
FACTURA_ID=285

echo "========================================"
echo "🚀 TESTING EN PRODUCCIÓN (RENDER)"
echo "========================================"

# Test 1: Verificar que el servidor está vivo
echo ""
echo "TEST 1: Health check"
echo "-----"
curl -s "$RENDER_URL/docs" | grep -q "FastAPI" && echo "✅ API disponible" || echo "❌ API no responde"

# Test 2: Estadísticas de tarifas
echo ""
echo "TEST 2: GET /debug/tarifas/stats"
echo "-----"
curl -s "$RENDER_URL/debug/tarifas/stats" | jq '.' || echo "❌ Error en endpoint"

# Test 3: Debug del comparador para factura 285
echo ""
echo "TEST 3: POST /debug/comparador/factura/285"
echo "-----"
curl -s -X POST "$RENDER_URL/debug/comparador/factura/$FACTURA_ID" | jq '.' || echo "❌ Error en endpoint"

# Test 4: Intentar generar PDF
echo ""
echo "TEST 4: GET /webhook/facturas/285/presupuesto.pdf"
echo "-----"
curl -s -I "$RENDER_URL/webhook/facturas/285/presupuesto.pdf" | head -5 || echo "❌ Error en endpoint"

echo ""
echo "========================================"
echo "✅ TESTING COMPLETADO"
echo "========================================"
