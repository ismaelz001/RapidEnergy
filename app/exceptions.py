"""
Excepciones de dominio para MECAENERGY CRM.
"""

class DomainError(Exception):
    """Error de dominio/negocio con código específico"""
    def __init__(self, code: str, message: str = None):
        self.code = code
        self.message = message or code
        super().__init__(self.message)
