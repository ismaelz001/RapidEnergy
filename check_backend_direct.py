import requests

backend_url = 'https://rapidenergy.onrender.com/api/clientes/365'

print("=== Testing Backend Directly (Render) ===")
try:
    # Test OPTIONS
    r = requests.options(backend_url, timeout=10)
    print(f'OPTIONS Status: {r.status_code}')
    print(f'Allow Header: {r.headers.get("Allow", "N/A")}')
    
    # Test DELETE (debería dar 401/403 sin auth, no 405)
    r2 = requests.delete(backend_url, timeout=10)
    print(f'\nDELETE Status: {r2.status_code}')
    print(f'Response: {r2.text[:200]}')
    
except Exception as e:
    print(f'Error: {e}')
