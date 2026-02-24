import requests

try:
    r = requests.options('https://energy.rodorte.com/api/clientes/365')
    print(f'Status: {r.status_code}')
    print(f'Allow: {r.headers.get("Allow", "N/A")}')
    print(f'Headers: {dict(r.headers)}')
except Exception as e:
    print(f'Error: {e}')
