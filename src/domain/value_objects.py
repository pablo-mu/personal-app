from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "EUR"

    def __add__(self, other):
        if not isinstance(other, Money):
            raise TypeError("Solo se puede sumar Money con Money")
        if self.currency != other.currency:
            raise ValueError("No se pueden sumar cantidades con diferentes monedas")
        return Money(self.amount + other.amount, self.currency)
    
    def __sub__(self, other):
        if not isinstance(other, Money):
            raise TypeError("Solo se puede restar Money con Money")
        if self.currency != other.currency:
            raise ValueError("No se pueden restar cantidades con diferentes monedas")
        return Money(self.amount - other.amount, self.currency)
    
    def is_zero(self):
        return self.amount == Decimal('0.00')

    def __neg__(self):
        """Permite usar el operador - (menos) delante de un objeto Money"""
        return Money(-self.amount, self.currency)
        
    @staticmethod
    def zero(currency: str = "EUR"):
        return Money(Decimal('0.00'), currency)