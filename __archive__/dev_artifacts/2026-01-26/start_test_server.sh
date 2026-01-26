#!/bin/bash

echo "🚀 Iniciando servidor de desarrollo para testing IVA..."
echo ""
echo "📋 Pasos del test:"
echo "1. Servidor arrancará en http://localhost:3000"
echo "2. Abre el navegador en esa URL"
echo "3. Sube una factura (temp_facturas/facturas/Factura Iberdrola.pdf)"
echo "4. Ve a Step 2 y verifica:"
echo "   - Selector de IVA con opciones 21%, 10%, 4%"
echo "   - Por defecto en 21%"
echo "   - Nota en impuesto eléctrico: (5.11269632% fijo)"
echo "5. Ve a Step 3 y compara"
echo "6. Abre consola del navegador (F12)"
echo "7. Busca en Network la respuesta de /comparar"
echo "8. Verifica que breakdown incluye:"
echo "   - modo_iva"
echo "   - modo_iee"
echo "   - modo_alquiler"
echo ""
echo "Arrancando servidor..."
echo ""

npm run dev
