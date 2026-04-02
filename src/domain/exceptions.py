"""
Excepciones del dominio de negocio.
 
Jerarquía:
  DomainException (base)
  ├── AccountError
  │   ├── AccountAlreadyExistsError
  │   ├── AccountNotFoundError
  │   ├── AccountHasTransactionsError
  │   ├── AccountTypeChangeError
  │   └── AccountHasBalanceError
  ├── TransactionError
  │   ├── TransactionNotFoundError
  │   └── TransactionImbalancedError
  ├── TagError
  │   ├── TagNotFoundError
  │   └── TagAlreadyExistsError
  ├── RecurringRuleError
  │   └── RecurringRuleNotFoundError
  └── ValidationError
      ├── CurrencyMismatchError
      └── NegativeAmountError
"""


class DomainException(Exception):
    """Clase base para todas las excepciones del dominio."""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


# ─────────────────────────────────────────
# Cuentas
# ─────────────────────────────────────────
 
class AccountError(DomainException):
    """Base para errores de cuentas."""


class AccountAlreadyExistsError(AccountError):
    """Se intenta crear una cuenta con nombre y tipo existentes"""
    def __init__(self, message:str):
        super.__init__(message, "ACCOUNT_ALREADY_EXISTS")


class AccountNotFoundError(AccountError):
    """La cuenta solicitada no existe."""
    def __init__(self, account_id=None, name: str = None):
        if account_id:
            msg = f"Cuenta con ID '{account_id}' no encontrada."
        elif name:
            msg = f"Cuenta '{name}' no encontrada."
        else:
            msg = "Cuenta no encontrada."
        super().__init__(msg, "ACCOUNT_NOT_FOUND")
 
 
class AccountHasTransactionsError(AccountError):
    """Se intenta eliminar o cambiar el tipo de una cuenta con transacciones."""
    def __init__(self, account_name: str, operation: str = "eliminar"):
        super().__init__(
            f"No se puede {operation} la cuenta '{account_name}' porque tiene transacciones asociadas.",
            "ACCOUNT_HAS_TRANSACTIONS",
        )
 
 
class AccountHasBalanceError(AccountError):
    """Se intenta eliminar una cuenta con saldo inicial distinto de cero."""
    def __init__(self, account_name: str):
        super().__init__(
            f"No se puede eliminar la cuenta '{account_name}' porque tiene saldo inicial. Ajústalo a cero primero.",
            "ACCOUNT_HAS_BALANCE",
        )
 
 
class AccountTypeChangeError(AccountError):
    """Se intenta cambiar el tipo de una cuenta que ya tiene movimientos."""
    def __init__(self, account_name: str):
        super().__init__(
            f"No se puede cambiar el tipo de la cuenta '{account_name}' porque ya tiene movimientos registrados.",
            "ACCOUNT_TYPE_CHANGE",
        )
 
 
# ─────────────────────────────────────────
# Transacciones
# ─────────────────────────────────────────
 
class TransactionError(DomainException):
    """Base para errores de transacciones."""
 
 
class TransactionNotFoundError(TransactionError):
    """La transacción solicitada no existe."""
    def __init__(self, transaction_id=None):
        msg = f"Transacción '{transaction_id}' no encontrada." if transaction_id else "Transacción no encontrada."
        super().__init__(msg, "TRANSACTION_NOT_FOUND")
 
 
class TransactionImbalancedError(TransactionError):
    """La transacción no está balanceada (principio de partida doble)."""
    def __init__(self, total_amount):
        super().__init__(
            f"La transacción está desbalanceada. Suma de apuntes: {total_amount} (debe ser 0).",
            "TRANSACTION_IMBALANCED",
        )
 
 
# ─────────────────────────────────────────
# Etiquetas
# ─────────────────────────────────────────
 
class TagError(DomainException):
    """Base para errores de etiquetas."""
 
 
class TagNotFoundError(TagError):
    """La etiqueta solicitada no existe."""
    def __init__(self, tag_id=None, name: str = None):
        if tag_id:
            msg = f"Etiqueta con ID '{tag_id}' no encontrada."
        elif name:
            msg = f"Etiqueta '{name}' no encontrada."
        else:
            msg = "Etiqueta no encontrada."
        super().__init__(msg, "TAG_NOT_FOUND")
 
 
class TagAlreadyExistsError(TagError):
    """Se intenta crear una etiqueta con nombre ya existente."""
    def __init__(self, name: str):
        super().__init__(f"La etiqueta '{name}' ya existe.", "TAG_ALREADY_EXISTS")
 
 
# ─────────────────────────────────────────
# Reglas Recurrentes
# ─────────────────────────────────────────
 
class RecurringRuleError(DomainException):
    """Base para errores de reglas recurrentes."""
 
 
class RecurringRuleNotFoundError(RecurringRuleError):
    """La regla recurrente solicitada no existe."""
    def __init__(self, rule_id=None):
        msg = f"Regla recurrente '{rule_id}' no encontrada." if rule_id else "Regla recurrente no encontrada."
        super().__init__(msg, "RECURRING_RULE_NOT_FOUND")
 
 
# ─────────────────────────────────────────
# Validación
# ─────────────────────────────────────────
 
class ValidationError(DomainException):
    """Base para errores de validación de dominio."""
 
 
class CurrencyMismatchError(ValidationError):
    """Las monedas de una operación no coinciden."""
    def __init__(self, expected: str, got: str):
        super().__init__(
            f"Inconsistencia de moneda: se esperaba '{expected}', se recibió '{got}'.",
            "CURRENCY_MISMATCH",
        )
 
 
class NegativeAmountError(ValidationError):
    """Un monto que debe ser positivo es negativo o cero."""
    def __init__(self, field: str = "monto"):
        super().__init__(
            f"El {field} debe ser mayor que cero.",
            "NEGATIVE_AMOUNT",
        )
 