#!/usr/bin/env python
import requests
r = requests.get('https://rapidenergy.onrender.com/webhook/facturas/285/presupuesto.pdf', timeout=20, allow_redirects=True)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    print(f'✅ PDF generado ({len(r.content)} bytes)')
    print(f'Content-Type: {r.headers.get("content-type")}')
    # Guardar para revisar
    with open('factura_285_test.pdf', 'wb') as f:
        f.write(r.content)
    print('Guardado como factura_285_test.pdf')
else:
    print(f'Status {r.status_code}')
    print(f'Response: {r.text[:300]}')
