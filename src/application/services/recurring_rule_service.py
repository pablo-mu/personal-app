"""
Servicio de Aplicación para Reglas Recurrentes.

Gestiona la lógica de negocio de periodicidad: cálculo de fechas,
ejecución automática y CRUD de reglas.
"""

import calendar
from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from dateutil.relativedelta import relativedelta

from src.application.dtos import (
    MoneySchema,
    RecurringRuleCreateDTO,
    RecurringRuleOutputDTO,
    RecurringRuleUpdateDTO,
    TransactionEntryDTO,
)
from src.application.ports import AbstractUnitOfWork
from src.domain.exceptions import AccountNotFoundError, RecurringRuleNotFoundError
from src.domain.models import (
    IntervalUnit,
    RecurrenceFrequency,
    RecurrenceType,
    RecurringRule,
)
from src.domain.value_objects import Money


class RecurringRuleService:
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    # ──────────────────────────────────────
    # Lógica de fechas (dominio puro)
    # ──────────────────────────────────────

    def calculate_next_execution_date(self, rule: RecurringRule) -> datetime:
        base = rule.last_execution_date or rule.start_date

        if rule.recurrence_type == RecurrenceType.INTERVAL_BASED:
            deltas = {
                IntervalUnit.DAYS:   timedelta(days=rule.interval_value),
                IntervalUnit.WEEKS:  timedelta(weeks=rule.interval_value),
                IntervalUnit.MONTHS: relativedelta(months=rule.interval_value),
                IntervalUnit.YEARS:  relativedelta(years=rule.interval_value),
            }
            return base + deltas[rule.interval_unit]

        # CALENDAR_BASED
        if rule.frequency == RecurrenceFrequency.DAILY:
            return base + timedelta(days=1)

        if rule.frequency == RecurrenceFrequency.WEEKLY:
            target  = rule.day_of_execution
            current = base.isoweekday()
            days_ahead = (target - current) % 7
            if days_ahead == 0:
                days_ahead = 7
            return base + timedelta(days=days_ahead)

        if rule.frequency == RecurrenceFrequency.MONTHLY:
            next_month = base + relativedelta(months=1)
            _, max_day = calendar.monthrange(next_month.year, next_month.month)
            actual_day = min(rule.day_of_execution, max_day)
            return next_month.replace(day=actual_day)

        if rule.frequency == RecurrenceFrequency.YEARLY:
            return base + relativedelta(years=1)

        raise ValueError(f"Configuración de recurrencia no soportada: {rule}")

    def should_execute_on(self, rule: RecurringRule, execution_date: datetime) -> bool:
        if not rule.is_active or rule.next_execution_date is None:
            return False
        if rule.end_date and execution_date.date() > rule.end_date.date():
            return False
        return execution_date.date() >= rule.next_execution_date.date()

    def mark_as_executed(self, rule: RecurringRule, execution_date: datetime) -> RecurringRule:
        temp = replace(rule, last_execution_date=execution_date, next_execution_date=None)
        next_date = self.calculate_next_execution_date(temp)
        return replace(temp, next_execution_date=next_date)

    def is_expired(self, rule: RecurringRule, current_date: datetime = None) -> bool:
        if rule.end_date is None:
            return False
        return (current_date or datetime.now()).date() > rule.end_date.date()

    def preview_executions(self, rule: RecurringRule, num_executions: int = 10) -> List[datetime]:
        dates = []
        current = rule
        for _ in range(num_executions):
            if not current.next_execution_date:
                break
            if rule.end_date and current.next_execution_date > rule.end_date:
                break
            dates.append(current.next_execution_date)
            current = self.mark_as_executed(current, current.next_execution_date)
        return dates

    # ──────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────

    def _to_output_dto(self, rule: RecurringRule, source_account, dest_account) -> RecurringRuleOutputDTO:
        return RecurringRuleOutputDTO(
            id=rule.id,
            description=rule.description,
            amount=MoneySchema(amount=rule.amount.amount, currency=rule.amount.currency),
            source_account_id=rule.source_account_id,
            destination_account_id=rule.destination_account_id,
            source_account_name=source_account.name if source_account else "Desconocido",
            destination_account_name=dest_account.name if dest_account else "Desconocido",
            transaction_type=rule.transaction_type,
            tags_ids=rule.tags_ids or [],
            recurrence_type=rule.recurrence_type,
            frequency=rule.frequency,
            day_of_execution=rule.day_of_execution,
            interval_value=rule.interval_value,
            interval_unit=rule.interval_unit,
            start_date=rule.start_date,
            end_date=rule.end_date,
            is_active=rule.is_active,
            last_execution_date=rule.last_execution_date,
            next_execution_date=rule.next_execution_date,
        )

    # ──────────────────────────────────────
    # CRUD
    # ──────────────────────────────────────

    def create_recurring_rule(self, dto: RecurringRuleCreateDTO) -> RecurringRuleOutputDTO:
        with self.uow:
            source = self.uow.accounts.get(dto.source_account_id)
            dest   = self.uow.accounts.get(dto.destination_account_id)
            if not source:
                raise AccountNotFoundError(dto.source_account_id)
            if not dest:
                raise AccountNotFoundError(dto.destination_account_id)

            description = dto.description or f"Transacción recurrente {source.name} → {dest.name}"
            new_rule = RecurringRule(
                id=uuid4(),
                description=description,
                amount=Money(dto.amount.amount, dto.amount.currency),
                source_account_id=dto.source_account_id,
                destination_account_id=dto.destination_account_id,
                transaction_type=dto.transaction_type,
                tags_ids=dto.tags_ids or [],
                recurrence_type=dto.recurrence_type,
                frequency=dto.frequency,
                day_of_execution=dto.day_of_execution,
                interval_value=dto.interval_value,
                interval_unit=dto.interval_unit,
                start_date=dto.start_date,
                end_date=dto.end_date,
                is_active=dto.is_active,
                last_execution_date=None,
                next_execution_date=None,
            )
            next_exec = self.calculate_next_execution_date(new_rule)
            new_rule  = replace(new_rule, next_execution_date=next_exec)

            self.uow.recurring_rules.add(new_rule)
            self.uow.commit()
            return self._to_output_dto(new_rule, source, dest)

    def update_recurring_rule(self, rule_id: UUID, dto: RecurringRuleUpdateDTO) -> RecurringRuleOutputDTO:
        with self.uow:
            rule = self.uow.recurring_rules.get(rule_id)
            if not rule:
                raise RecurringRuleNotFoundError(rule_id)

            changes = {}
            if dto.description is not None:
                changes["description"] = dto.description
            if dto.amount is not None:
                changes["amount"] = Money(dto.amount.amount, dto.amount.currency)
            if dto.tags_ids is not None:
                changes["tags_ids"] = dto.tags_ids
            if dto.end_date is not None:
                changes["end_date"] = dto.end_date
            if dto.is_active is not None:
                changes["is_active"] = dto.is_active

            updated = replace(rule, **changes)

            # Recalcular próxima ejecución si cambiaron parámetros relevantes
            if ("end_date" in changes or "is_active" in changes) and updated.is_active and not self.is_expired(updated):
                next_exec = self.calculate_next_execution_date(updated)
                updated   = replace(updated, next_execution_date=next_exec)

            self.uow.recurring_rules.update(updated)
            self.uow.commit()

            source = self.uow.accounts.get(updated.source_account_id)
            dest   = self.uow.accounts.get(updated.destination_account_id)
            return self._to_output_dto(updated, source, dest)

    def delete_recurring_rule(self, rule_id: UUID) -> None:
        with self.uow:
            if not self.uow.recurring_rules.get(rule_id):
                raise RecurringRuleNotFoundError(rule_id)
            self.uow.recurring_rules.delete(rule_id)
            self.uow.commit()

    def get_recurring_rule(self, rule_id: UUID) -> RecurringRuleOutputDTO:
        with self.uow:
            rule = self.uow.recurring_rules.get(rule_id)
            if not rule:
                raise RecurringRuleNotFoundError(rule_id)
            source = self.uow.accounts.get(rule.source_account_id)
            dest   = self.uow.accounts.get(rule.destination_account_id)
            return self._to_output_dto(rule, source, dest)

    def list_recurring_rules(self, active_only: bool = False) -> List[RecurringRuleOutputDTO]:
        with self.uow:
            rules = self.uow.recurring_rules.get_active_rules() if active_only else self.uow.recurring_rules.get_all()
            result = []
            for rule in rules:
                source = self.uow.accounts.get(rule.source_account_id)
                dest   = self.uow.accounts.get(rule.destination_account_id)
                result.append(self._to_output_dto(rule, source, dest))
            return result

    # ──────────────────────────────────────
    # Ejecución automática
    # ──────────────────────────────────────

    def execute_pending_rules(self, execution_date: datetime, transaction_service) -> List[dict]:
        """
        Ejecuta todas las reglas cuya próxima ejecución sea ≤ execution_date.

        Diseño de UoW:
        ─────────────
        No se anidan bloques 'with self.uow' porque ambos servicios comparten
        la misma instancia de UoW. Anidarlos sobreescribiría la sesión activa.

        En su lugar se usan tres fases secuenciales con bloques independientes:
          1. Leer reglas pendientes  (UoW propio → cerrado)
          2. Por cada regla: crear transacción (UoW del TransactionService)
          3. Actualizar el estado de la regla  (UoW propio → cerrado)
        """
        # ── FASE 1: Leer reglas pendientes ────────────────────────────────────
        with self.uow:
            all_rules = self.uow.recurring_rules.get_all()

        pending     = [r for r in all_rules if self.should_execute_on(r, execution_date)]
        created_txs = []

        for rule in pending:
            try:
                # ── FASE 2: Crear transacción (UoW del TransactionService) ────
                tx_dto = TransactionEntryDTO(
                    description=f"🔁 {rule.description}",
                    amount=MoneySchema(amount=rule.amount.amount, currency=rule.amount.currency),
                    source_account_id=rule.source_account_id,
                    destination_account_id=rule.destination_account_id,
                    date=execution_date,
                    tags_ids=rule.tags_ids or [],
                )
                created_tx = transaction_service.create_transaction(tx_dto)

                # ── FASE 3: Actualizar estado de la regla (UoW propio) ────────
                updated_rule = self.mark_as_executed(rule, execution_date)
                with self.uow:
                    self.uow.recurring_rules.update(updated_rule)
                    self.uow.commit()

                created_txs.append({
                    "rule_id": str(rule.id),
                    "rule_description": rule.description,
                    "transaction_id": str(created_tx.id),
                    "amount": float(created_tx.amount.amount),
                    "next_execution": (
                        updated_rule.next_execution_date.isoformat()
                        if updated_rule.next_execution_date else None
                    ),
                })

            except Exception as e:
                print(f"❌ Error ejecutando regla '{rule.description}': {e}")

        return created_txs