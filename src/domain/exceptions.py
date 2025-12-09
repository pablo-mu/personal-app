"""
Source domain exceptions.
"""

class AccountError(Exception):
    """Clase base para excepciones relacionadas con cuentas."""
    pass

class AccountAlreadyExistsError(AccountError):
    """Excepción lanzada cuando se intenta crear una cuenta que ya existe."""
    pass