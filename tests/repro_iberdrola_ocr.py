
import sys
import os
import unittest
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ocr import parse_invoice_text

class TestIberdrolaOCR(unittest.TestCase):
    def test_iberdrola_parsing(self):
        # Raw text simulated from user description
        raw_text = """
        Datos del contrato
        Titular: Juan Cliente
        NIF: 12345678A
        Dirección de suministro: Calle Falsa 123, Madrid
        
        Identificación punto de suministro (CUPS): ES 0031 4050 6789 0123 AB 1F
        Peaje de acceso de transporte y distribución (ATR): 2.0TD
        Potencia contratada: Punta 4,600 kW Valle 4,600 kW
        
        Información del consumo
        PERIODO DE FACTURACIÓN: 31/08/2025 - 30/09/2025
        DIAS FACTURADOS: 30
        
        Sus consumos desagregados han sido punta: 59 kWh; llano: 55,99 kWh; valle 166,72 kWh.
        
        Importes
        IMPORTE TOTAL 32,13 €
        IVA (21%) 6,75 €
        TOTAL IMPORTE FACTURA 38,88 €
        """
        
        result = parse_invoice_text(raw_text)
        
        print("\n--- OCR RESULT ---")
        print(f"CUPS: {result.get('cups')}")
        print(f"ATR: {result.get('atr')}")
        print(f"Consumo P1: {result.get('consumo_p1_kwh')}")
        print(f"Consumo P2: {result.get('consumo_p2_kwh')}")
        print(f"Consumo P3: {result.get('consumo_p3_kwh')}")
        print(f"Total Factura: {result.get('total_factura')}")
        print(f"Días Facturados: {result.get('parsed_fields', {}).get('dias_facturados', 'N/A')}") # Custom field checking
        print(f"Fechas: {result.get('fecha_inicio_consumo')} - {result.get('fecha_fin_consumo')}")
        
        # Assertions
        # 1. CUPS with spaces
        normalized_cups = result.get('cups', '').replace(" ", "").strip()
        self.assertEqual(normalized_cups, "ES0031405067890123AB1F", "CUPS extraction failed")
        
        # 2. Consumption mapping (Punta->P1, Llano->P2, Valle->P3)
        self.assertEqual(result.get('consumo_p1_kwh'), 59.0, "Consumo P1 (Punta) failed")
        self.assertEqual(result.get('consumo_p2_kwh'), 55.99, "Consumo P2 (Llano) failed")
        self.assertEqual(result.get('consumo_p3_kwh'), 166.72, "Consumo P3 (Valle) failed")
        
        # 3. Total Factura precedence
        self.assertEqual(result.get('total_factura'), 38.88, "Total Factura should be 38.88")
        
        # 4. Dates
        self.assertEqual(result.get('fecha_inicio_consumo'), "31/08/2025")
        self.assertEqual(result.get('fecha_fin_consumo'), "30/09/2025")

if __name__ == '__main__':
    unittest.main()
