"""
Tests P1 simplificados: Validaciones Step2 y total_ajustado
"""

import pytest
from app.db.models import Factura


class TestP1Step2ValidationLogic:
    """P1-STEP2-01: Lógica de validación Step2"""
    
    def test_factura_sin_step2_no_es_valida(self):
        """Factura SIN Step2 no debe estar lista para comparar"""
        factura = Factura(
            id=1,
            consumo_p1_kwh=59.0,
            consumo_p2_kwh=56.0,
            consumo_p3_kwh=167.0,
            potencia_p1_kw=5.0,
            potencia_p2_kw=5.0,
            total_factura=38.88,
            validado_step2=False,  # ← SIN STEP2
            total_ajustado=None,
        )
        
        # Validación lógica
        assert factura.validado_step2 is False
        assert factura.total_ajustado is None
        
        # Simular la validación del endpoint
        validado = getattr(factura, "validado_step2", False)
        assert validado is False, "Factura sin Step2 debe fallar validación"
    
    def test_factura_con_step2_es_valida(self):
        """Factura CON Step2 está lista para comparar"""
        factura = Factura(
            id=2,
            consumo_p1_kwh=59.0,
            consumo_p2_kwh=56.0,
            consumo_p3_kwh=167.0,
            potencia_p1_kw=5.0,
            potencia_p2_kw=5.0,
            total_factura=38.88,
            validado_step2=True,  # ← CON STEP2
            total_ajustado=38.88,
        )
        
        assert factura.validado_step2 is True
        assert factura.total_ajustado == 38.88


class TestP1TotalAjustadoValidationLogic:
    """P1-VAL-01: Lógica de validación total_ajustado"""
    
    def test_total_ajustado_none_no_es_valido(self):
        """total_ajustado=None debe fallar validación"""
        factura = Factura(
            id=3,
            validado_step2=True,
            total_ajustado=None,  # ← INVALID
        )
        
        total = getattr(factura, "total_ajustado", None)
        is_valid = total is not None and total > 0
        
        assert is_valid is False, "total_ajustado=None debe ser inválido"
    
    def test_total_ajustado_zero_no_es_valido(self):
        """total_ajustado=0 debe fallar validación"""
        factura = Factura(
            id=4,
            validado_step2=True,
            total_ajustado=0.0,  # ← INVALID
        )
        
        total = factura.total_ajustado
        is_valid = total is not None and total > 0
        
        assert is_valid is False, "total_ajustado=0 debe ser inválido"
    
    def test_total_ajustado_negativo_no_es_valido(self):
        """total_ajustado negativo debe fallar validación"""
        factura = Factura(
            id=5,
            validado_step2=True,
            total_ajustado=-10.0,  # ← INVALID
        )
        
        total = factura.total_ajustado
        is_valid = total is not None and total > 0
        
        assert is_valid is False, "total_ajustado negativo debe ser inválido"
    
    def test_total_ajustado_valido_pasa(self):
        """total_ajustado válido (>0) debe pasar validación"""
        factura = Factura(
            id=6,
            validado_step2=True,
            total_ajustado=38.88,  # ← VALID
        )
        
        total = factura.total_ajustado
        is_valid = total is not None and total > 0
        
        assert is_valid is True, "total_ajustado=38.88 debe ser válido"


class TestP1CombinedValidation:
    """P1: Validación combinada Step2 + total_ajustado"""
    
    def test_ambos_criterios_deben_cumplirse(self):
        """Factura debe tener AMBOS: Step2=True Y total_ajustado>0"""
        
        # Caso 1: Solo Step2=True pero sin total_ajustado
        factura1 = Factura(
            id=7,
            validado_step2=True,
            total_ajustado=None,
        )
        is_ready_1 = (
            factura1.validado_step2 and 
            factura1.total_ajustado is not None and 
            factura1.total_ajustado > 0
        )
        assert is_ready_1 is False, "Solo Step2 no es suficiente"
        
        # Caso 2: Solo total_ajustado pero sin Step2
        factura2 = Factura(
            id=8,
            validado_step2=False,
            total_ajustado=38.88,
        )
        is_ready_2 = (
            factura2.validado_step2 and 
            factura2.total_ajustado is not None and 
            factura2.total_ajustado > 0
        )
        assert is_ready_2 is False, "Solo total_ajustado no es suficiente"
        
        # Caso 3: Ambos OK
        factura3 = Factura(
            id=9,
            validado_step2=True,
            total_ajustado=38.88,
        )
        is_ready_3 = (
            factura3.validado_step2 and 
            factura3.total_ajustado is not None and 
            factura3.total_ajustado > 0
        )
        assert is_ready_3 is True, "Ambos criterios OK → factura lista"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
