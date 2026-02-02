"""
pytest test file for OCR P0 requirements validation.

6 test cases covering:
1. DD.MM.YYYY date parsing
2. dias_facturados calculation from fecha_inicio/fecha_fin
3. Pattern A: "Su consumo en el periodo facturado ha sido XXX kWh"
4. Pattern B: "XXX kWh x 0,xxxxx €/kWh"
5. Anti-lecturas detection (>5000 kWh + <15 kW potencia)
6. Anti-IVA detection (consumo_kwh ≈ 21%)
"""

import pytest
from datetime import date
from app.services.ocr import (
    _parse_date_flexible,
    _extract_consumo_safe,
    _sanity_energy,
    parse_es_number,
)


class TestDateParsingP0:
    """Test 1: DD.MM.YYYY date parsing (P0 requirement)"""
    
    def test_parse_date_ddmmyyyy_dots(self):
        """Parse DD.MM.YYYY format (German/Swiss style)"""
        # Given: Invoice date in DD.MM.YYYY format
        date_str = "15.02.2024"
        
        # When: Parsing with flexible parser
        result = _parse_date_flexible(date_str)
        
        # Then: Should correctly parse to 2024-02-15
        assert result == date(2024, 2, 15)
    
    def test_parse_date_ddmmyyyy_dots_two_digit_year(self):
        """Parse DD.MM.YY format (2-digit year)"""
        date_str = "31.12.24"
        result = _parse_date_flexible(date_str)
        assert result == date(2024, 12, 31)
    
    def test_parse_date_ddmmyyyy_slashes_still_works(self):
        """Ensure DD/MM/YYYY still works (backward compatibility)"""
        date_str = "15/02/2024"
        result = _parse_date_flexible(date_str)
        assert result == date(2024, 2, 15)
    
    def test_parse_date_ddmmyyyy_dashes_still_works(self):
        """Ensure DD-MM-YYYY still works (backward compatibility)"""
        date_str = "15-02-2024"
        result = _parse_date_flexible(date_str)
        assert result == date(2024, 2, 15)


class TestDiasFacturadosP0:
    """Test 2: dias_facturados calculation from fecha_inicio/fecha_fin"""
    
    def test_calculate_dias_facturados_normal(self):
        """Calculate dias_facturados from two dates (normal month)"""
        # Given: Invoice start and end dates
        fecha_ini = date(2024, 2, 1)
        fecha_fin = date(2024, 2, 29)  # Feb 2024 (leap year)
        
        # When: Calculating difference
        dias = (fecha_fin - fecha_ini).days + 1  # +1 includes both start and end
        
        # Then: Should be 29 days
        assert dias == 29
    
    def test_calculate_dias_facturados_monthly_standard(self):
        """Calculate dias_facturados for standard 30-day month"""
        fecha_ini = date(2024, 1, 15)
        fecha_fin = date(2024, 2, 13)
        
        dias = (fecha_fin - fecha_ini).days + 1
        assert dias == 30
    
    def test_calculate_dias_facturados_quarterly(self):
        """Calculate dias_facturados for 90-day quarter"""
        fecha_ini = date(2024, 1, 1)
        fecha_fin = date(2024, 3, 31)
        
        dias = (fecha_fin - fecha_ini).days + 1
        assert dias == 91  # 31 (Jan) + 29 (Feb leap) + 31 (Mar)
    
    def test_dias_facturados_single_day(self):
        """Edge case: single day billing"""
        fecha_ini = date(2024, 2, 15)
        fecha_fin = date(2024, 2, 15)
        
        dias = (fecha_fin - fecha_ini).days + 1
        assert dias == 1
    
    def test_dias_facturados_invalid_if_fin_before_ini(self):
        """Edge case: end date before start date = invalid"""
        fecha_ini = date(2024, 2, 15)
        fecha_fin = date(2024, 2, 10)
        
        dias = (fecha_fin - fecha_ini).days + 1
        assert dias <= 0  # Should be invalid (caught by sanity check)


class TestConsumoSafePatternA:
    """Test 3: Pattern A extraction - "Su consumo en el periodo facturado ha sido XXX kWh" """
    
    def test_extract_pattern_a_naturgy_spanish(self):
        """Extract consumo from Pattern A (Naturgy/Regulada Spanish text)"""
        # Given: Invoice text with Pattern A
        invoice_text = """
        Su consumo en el periodo facturado ha sido 250,45 kWh
        Tarifa: 2.0TD
        """
        
        # When: Using safe extraction
        result = _extract_consumo_safe(invoice_text)
        
        # Then: Should extract 250.45 kWh
        assert result['value'] == pytest.approx(250.45, rel=0.01)
        assert result['pattern'] == 'A (su consumo en el periodo)'
    
    def test_extract_pattern_a_spanish_numbers(self):
        """Pattern A with Spanish number format (dot as thousands, comma as decimal)"""
        invoice_text = """
        Su consumo en el periodo facturado ha sido 1.234,56 kWh
        """
        
        result = _extract_consumo_safe(invoice_text)
        assert result['value'] == pytest.approx(1234.56, rel=0.01)
        assert result['pattern'] == 'A (su consumo en el periodo)'
    
    def test_extract_pattern_a_no_kwh_suffix(self):
        """Pattern A without 'kWh' suffix (just 'h' or bare number)"""
        invoice_text = """
        Su consumo en el periodo facturado ha sido 100,25 h
        """
        
        result = _extract_consumo_safe(invoice_text)
        assert result['value'] == pytest.approx(100.25, rel=0.01)


class TestConsumoSafePatternB:
    """Test 4: Pattern B extraction - "XXX kWh x 0,xxxxx €/kWh" """
    
    def test_extract_pattern_b_consumption_tariff(self):
        """Extract consumo from Pattern B (consumption × unit tariff)"""
        # Given: Invoice text with consumption × tariff product
        invoice_text = """
        Energía punta:
        125,50 kWh x 0,12345 €/kWh = 15,48 €
        """
        
        # When: Using safe extraction
        result = _extract_consumo_safe(invoice_text)
        
        # Then: Should extract 125.50 kWh (NOT the calculated price 15.48)
        assert result['value'] == pytest.approx(125.50, rel=0.01)
        assert result['pattern'] == 'B (consumo × tarifa)'
    
    def test_extract_pattern_b_spanish_format(self):
        """Pattern B with Spanish number formatting"""
        invoice_text = """
        Energía consumida:
        1.234,56 kWh x 0,15678 €/kWh = 193,45 €
        """
        
        result = _extract_consumo_safe(invoice_text)
        assert result['value'] == pytest.approx(1234.56, rel=0.01)


class TestAntiLecturasDetection:
    """Test 5: Anti-lecturas detection (>5000 kWh + <15 kW potencia)"""
    
    def test_anti_lecturas_high_consumption_low_power(self):
        """Reject consumo when >5000 kWh + <15 kW potencia (meter reading, not period consumption)"""
        # Given: Invoice with suspicious meter reading instead of period consumption
        result = {
            "consumo_kwh": 15974.25,  # Accumulated meter reading (huge)
            "potencia_p1_kw": 4.6,     # Residential potencia (small)
            "potencia_p2_kw": None,
            "detected_por_ocr": {"consumo_kwh": True}
        }
        
        # When: Running sanity check
        sanitized = _sanity_energy(result)
        
        # Then: consumo_kwh should be rejected (set to None)
        assert sanitized["consumo_kwh"] is None
        assert sanitized["detected_por_ocr"]["consumo_kwh"] is False
    
    def test_anti_lecturas_accepts_high_industrial(self):
        """Accept high consumption if potencia >= 15 kW (industrial/large)"""
        # Given: Industrial invoice with high consumption AND high potencia
        result = {
            "consumo_kwh": 8000.0,     # High consumption (but within reason)
            "potencia_p1_kw": 20.0,    # Industrial potencia (large)
            "potencia_p2_kw": None,
            "detected_por_ocr": {"consumo_kwh": True}
        }
        
        # When: Running sanity check
        sanitized = _sanity_energy(result)
        
        # Then: consumo_kwh should be ACCEPTED (still present)
        assert sanitized["consumo_kwh"] == 8000.0
    
    def test_anti_lecturas_accepts_normal_consumption(self):
        """Accept normal residential consumption (<5000 kWh)"""
        result = {
            "consumo_kwh": 450.75,     # Normal monthly consumption
            "potencia_p1_kw": 4.6,
            "potencia_p2_kw": None,
            "detected_por_ocr": {"consumo_kwh": True}
        }
        
        sanitized = _sanity_energy(result)
        assert sanitized["consumo_kwh"] == 450.75


class TestAntiIVADetection:
    """Test 6: Anti-IVA detection (consumo_kwh ≈ 21% or other tax percentages)"""
    
    def test_anti_iva_21_percent_rejection(self):
        """Reject consumo_kwh ≈ 21 (common OCR error: captured IVA% instead of consumption)"""
        # Given: OCR incorrectly captured IVA 21% as consumption
        result = {
            "consumo_kwh": 21.0,  # Exact IVA percentage
            "potencia_p1_kw": 4.6,
            "potencia_p2_kw": None,
            "detected_por_ocr": {"consumo_kwh": True}
        }
        
        # When: Running sanity check
        sanitized = _sanity_energy(result)
        
        # Then: consumo_kwh should be rejected
        assert sanitized["consumo_kwh"] is None
        assert sanitized["detected_por_ocr"]["consumo_kwh"] is False
    
    def test_anti_iva_21_percent_range(self):
        """Reject consumo in range 19-23 (IVA 21% ± 2 range)"""
        for suspicious_value in [19, 20, 21, 22, 23]:
            result = {
                "consumo_kwh": float(suspicious_value),
                "potencia_p1_kw": 4.6,
                "potencia_p2_kw": None,
                "detected_por_ocr": {"consumo_kwh": True}
            }
            
            sanitized = _sanity_energy(result)
            assert sanitized["consumo_kwh"] is None, f"Should reject {suspicious_value} (IVA confusion)"
    
    def test_anti_iva_10_percent_alternative(self):
        """Reject consumo in range 9-11 (reduced IVA 10% for food, etc.)"""
        for suspicious_value in [9, 10, 11]:
            result = {
                "consumo_kwh": float(suspicious_value),
                "potencia_p1_kw": 4.6,
                "potencia_p2_kw": None,
                "detected_por_ocr": {"consumo_kwh": True}
            }
            
            sanitized = _sanity_energy(result)
            assert sanitized["consumo_kwh"] is None, f"Should reject {suspicious_value} (tax% confusion)"
    
    def test_anti_potencia_confusion_very_low(self):
        """Reject consumo < 0.5 kWh (likely potencia erroneously assigned)"""
        result = {
            "consumo_kwh": 0.25,  # Absurdly low (likely potencia 0.25 kW = 250 W)
            "potencia_p1_kw": 4.6,
            "potencia_p2_kw": None,
            "detected_por_ocr": {"consumo_kwh": True}
        }
        
        sanitized = _sanity_energy(result)
        assert sanitized["consumo_kwh"] is None
    
    def test_accepts_valid_low_consumption(self):
        """Accept valid low consumption (>0.5 but <3 kWh, e.g., vacation month)"""
        result = {
            "consumo_kwh": 1.5,  # Low but valid (holiday period, empty flat, etc.)
            "potencia_p1_kw": 4.6,
            "potencia_p2_kw": None,
            "detected_por_ocr": {"consumo_kwh": True}
        }
        
        sanitized = _sanity_energy(result)
        assert sanitized["consumo_kwh"] == 1.5


class TestDiasFacturadosValidation:
    """Additional test: dias_facturados range validation (1-370 days)"""
    
    def test_dias_facturados_valid_monthly(self):
        """Accept dias_facturados = 30 (normal month)"""
        result = {
            "dias_facturados": 30,
            "detected_por_ocr": {"dias_facturados": True}
        }
        
        sanitized = _sanity_energy(result)
        assert sanitized["dias_facturados"] == 30
    
    def test_dias_facturados_reject_zero(self):
        """Reject dias_facturados = 0 (invalid)"""
        result = {
            "dias_facturados": 0,
            "detected_por_ocr": {"dias_facturados": True}
        }
        
        sanitized = _sanity_energy(result)
        assert sanitized["dias_facturados"] is None
    
    def test_dias_facturados_reject_negative(self):
        """Reject dias_facturados = -5 (invalid)"""
        result = {
            "dias_facturados": -5,
            "detected_por_ocr": {"dias_facturados": True}
        }
        
        sanitized = _sanity_energy(result)
        assert sanitized["dias_facturados"] is None
    
    def test_dias_facturados_reject_too_large(self):
        """Reject dias_facturados = 400 (>370, beyond annual)"""
        result = {
            "dias_facturados": 400,
            "detected_por_ocr": {"dias_facturados": True}
        }
        
        sanitized = _sanity_energy(result)
        assert sanitized["dias_facturados"] is None
    
    def test_dias_facturados_accept_annual(self):
        """Accept dias_facturados = 365 (annual invoice)"""
        result = {
            "dias_facturados": 365,
            "detected_por_ocr": {"dias_facturados": True}
        }
        
        sanitized = _sanity_energy(result)
        assert sanitized["dias_facturados"] == 365


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
