from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from dataclasses import replace

from src.application.ports import AbstractRecurringRuleRepository
from src.domain.models import RecurringRule, RecurrenceType, RecurrenceFrequency, IntervalUnit, TransactionType
from src.domain.value_objects import Money
from src.infrastructure.persistence.models import RecurringRuleModel, TagModel

class SQLAlchemyRecurringRuleRepository(AbstractRecurringRuleRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, rule: RecurringRule) -> None:
        """Añade una nueva regla recurrente."""
        model = RecurringRuleModel(
            id=str(rule.id),
            description=rule.description,
            amount=rule.amount.amount,
            currency=rule.amount.currency,
            source_account_id=str(rule.source_account_id),
            destination_account_id=str(rule.destination_account_id),
            transaction_type=rule.transaction_type.value,
            recurrence_type=rule.recurrence_type.value,
            frequency=rule.frequency.value if rule.frequency else None,
            day_of_execution=rule.day_of_execution,
            interval_value=rule.interval_value,
            interval_unit=rule.interval_unit.value if rule.interval_unit else None,
            start_date=rule.start_date,
            end_date=rule.end_date,
            is_active=1 if rule.is_active else 0,
            last_execution_date=rule.last_execution_date,
            next_execution_date=rule.next_execution_date
        )
        
        # Asociar tags
        if rule.tags_ids:
            tags = self.session.query(TagModel).filter(TagModel.id.in_([str(t) for t in rule.tags_ids])).all()
            model.tags = tags
        
        self.session.add(model)

    def get(self, entity_id: UUID) -> Optional[RecurringRule]:
        """Obtiene una regla por ID."""
        model = self.session.query(RecurringRuleModel).filter_by(id=str(entity_id)).first()
        if not model:
            return None
        return self._to_domain(model)

    def list(self) -> List[RecurringRule]:
        """Obtiene todas las reglas."""
        models = self.session.query(RecurringRuleModel).all()
        return [self._to_domain(model) for model in models]
    
    def get_all(self) -> List[RecurringRule]:
        """Obtiene todas las reglas (alias de list)."""
        return self.list()

    def get_active_rules(self) -> List[RecurringRule]:
        """Obtiene solo las reglas activas."""
        models = self.session.query(RecurringRuleModel).filter_by(is_active=1).all()
        return [self._to_domain(model) for model in models]

    def update(self, rule: RecurringRule) -> None:
        """Actualiza una regla existente."""
        model = self.session.query(RecurringRuleModel).filter_by(id=str(rule.id)).first()
        if not model:
            raise ValueError(f"Regla con ID {rule.id} no encontrada")
        
        # Actualizar campos
        model.description = rule.description
        model.amount = rule.amount.amount
        model.currency = rule.amount.currency
        model.source_account_id = str(rule.source_account_id)
        model.destination_account_id = str(rule.destination_account_id)
        model.transaction_type = rule.transaction_type.value
        model.recurrence_type = rule.recurrence_type.value
        model.frequency = rule.frequency.value if rule.frequency else None
        model.day_of_execution = rule.day_of_execution
        model.interval_value = rule.interval_value
        model.interval_unit = rule.interval_unit.value if rule.interval_unit else None
        model.start_date = rule.start_date
        model.end_date = rule.end_date
        model.is_active = 1 if rule.is_active else 0
        model.last_execution_date = rule.last_execution_date
        model.next_execution_date = rule.next_execution_date
        
        # Actualizar tags
        if rule.tags_ids is not None:
            tags = self.session.query(TagModel).filter(TagModel.id.in_([str(t) for t in rule.tags_ids])).all()
            model.tags = tags
        
        self.session.add(model)

    def delete(self, entity_id: UUID) -> None:
        """Elimina una regla."""
        model = self.session.query(RecurringRuleModel).filter_by(id=str(entity_id)).first()
        if model:
            self.session.delete(model)

    def _to_domain(self, model: RecurringRuleModel) -> RecurringRule:
        """Convierte modelo de persistencia a entidad de dominio."""
        return RecurringRule(
            id=UUID(model.id),
            description=model.description,
            amount=Money(model.amount, model.currency),
            source_account_id=UUID(model.source_account_id),
            destination_account_id=UUID(model.destination_account_id),
            transaction_type=TransactionType(model.transaction_type),
            tags_ids=[UUID(tag.id) for tag in model.tags] if model.tags else [],
            recurrence_type=RecurrenceType(model.recurrence_type),
            frequency=RecurrenceFrequency(model.frequency) if model.frequency else None,
            day_of_execution=model.day_of_execution,
            interval_value=model.interval_value,
            interval_unit=IntervalUnit(model.interval_unit) if model.interval_unit else None,
            start_date=model.start_date,
            end_date=model.end_date,
            is_active=bool(model.is_active),
            last_execution_date=model.last_execution_date,
            next_execution_date=model.next_execution_date
        )
