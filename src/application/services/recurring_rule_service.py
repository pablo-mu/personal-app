from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4
from dataclasses import replace
import calendar
from dateutil.relativedelta import relativedelta

from src.application.ports import AbstractUnitOfWork
from src.application.dtos import (
    RecurringRuleCreateDTO,
    RecurringRuleUpdateDTO,
    RecurringRuleOutputDTO,
    MoneySchema,
    TransactionEntryDTO
)
from src.domain.models import (
    RecurringRule,
    RecurrenceType,
    RecurrenceFrequency,
    IntervalUnit
)
from src.domain.value_objects import Money


class RecurringRuleService:
    """
    Servicio de aplicación para gestionar reglas recurrentes.
    Contiene toda la lógica de negocio relacionada con periodizaciones.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    # =========================================
    # LÓGICA DE CÁLCULO DE FECHAS
    # =========================================

    def calculate_next_execution_date(self, rule: RecurringRule) -> datetime:
        """
        Calcula la próxima fecha de ejecución basada en la configuración.
        LÓGICA DE NEGOCIO: Cómo determinar cuándo ejecutar una regla.
        """
        base_date = rule.last_execution_date or rule.start_date

        if rule.recurrence_type == RecurrenceType.INTERVAL_BASED:
            # Intervalo desde última ejecución
            if rule.interval_unit == IntervalUnit.DAYS:
                return base_date + timedelta(days=rule.interval_value)
            elif rule.interval_unit == IntervalUnit.WEEKS:
                return base_date + timedelta(weeks=rule.interval_value)
            elif rule.interval_unit == IntervalUnit.MONTHS:
                return base_date + relativedelta(months=rule.interval_value)
            elif rule.interval_unit == IntervalUnit.YEARS:
                return base_date + relativedelta(years=rule.interval_value)

        elif rule.recurrence_type == RecurrenceType.CALENDAR_BASED:
            # Anclado al calendario
            if rule.frequency == RecurrenceFrequency.MONTHLY:
                next_month = base_date + relativedelta(months=1)

                # Ajustar día al máximo disponible en el mes (ej: 31 → 28 feb)
                _, max_day = calendar.monthrange(next_month.year, next_month.month)
                actual_day = min(rule.day_of_execution, max_day)

                return next_month.replace(day=actual_day)

            elif rule.frequency == RecurrenceFrequency.WEEKLY:
                target_weekday = rule.day_of_execution
                current_weekday = base_date.isoweekday()

                # Calcular días hasta el próximo día objetivo
                days_ahead = (target_weekday - current_weekday) % 7

                # Si es el mismo día y ya ejecutamos, ir a próxima semana
                if days_ahead == 0:
                    if rule.last_execution_date and base_date.date() == rule.last_execution_date.date():
                        days_ahead = 7
                    elif base_date.date() != rule.start_date.date():
                        days_ahead = 7

                return base_date + timedelta(days=days_ahead)

            elif rule.frequency == RecurrenceFrequency.DAILY:
                return base_date + timedelta(days=1)
            elif rule.frequency == RecurrenceFrequency.YEARLY:
                return base_date + relativedelta(years=1)

        raise ValueError(f"Tipo de recurrencia no soportado: {rule.recurrence_type}")

    def should_execute_on(self, rule: RecurringRule, execution_date: datetime) -> bool:
        """
        LÓGICA DE NEGOCIO: Determina si una regla debe ejecutarse en cierta fecha.
        Considera estado activo, fechas límite, y próxima ejecución programada.
        """
        if not rule.is_active:
            return False

        if rule.next_execution_date is None:
            return False

        # Validar límite temporal
        if rule.end_date is not None and execution_date.date() > rule.end_date.date():
            return False

        return execution_date.date() >= rule.next_execution_date.date()

    def mark_as_executed(self, rule: RecurringRule, execution_date: datetime) -> RecurringRule:
        """
        LÓGICA DE NEGOCIO: Marca una regla como ejecutada y calcula próxima fecha.
        Retorna una copia actualizada de la regla (inmutabilidad).
        """
        # Calcular próxima ejecución
        updated_rule = replace(
            rule,
            last_execution_date=execution_date,
            next_execution_date=None  # Temporal
        )

        next_date = self.calculate_next_execution_date(updated_rule)

        return replace(updated_rule, next_execution_date=next_date)

    def is_expired(self, rule: RecurringRule, current_date: datetime = None) -> bool:
        """
        LÓGICA DE NEGOCIO: Determina si una regla ha expirado.
        """
        if rule.end_date is None:
            return False

        current = current_date or datetime.now()
        return current.date() > rule.end_date.date()

    def preview_executions(self, rule: RecurringRule, num_executions: int = 5) -> List[datetime]:
        """
        LÓGICA DE PRESENTACIÓN: Calcula las próximas N fechas de ejecución.
        Útil para mostrar en UI sin modificar la regla real.
        """
        dates = []
        current_rule = rule

        for _ in range(num_executions):
            if current_rule.next_execution_date is None:
                break
            if rule.end_date and current_rule.next_execution_date > rule.end_date:
                break

            dates.append(current_rule.next_execution_date)
            current_rule = self.mark_as_executed(current_rule, current_rule.next_execution_date)

        return dates

    # =========================================
    # OPERACIONES CRUD
    # =========================================

    def create_recurring_rule(self, dto: RecurringRuleCreateDTO) -> RecurringRuleOutputDTO:
        """Crea una nueva regla recurrente."""
        with self.uow:
            # Validaciones de negocio
            source_account = self.uow.accounts.get(dto.source_account_id)
            dest_account = self.uow.accounts.get(dto.destination_account_id)

            if not source_account:
                raise ValueError(f"Cuenta origen {dto.source_account_id} no existe")
            if not dest_account:
                raise ValueError(f"Cuenta destino {dto.destination_account_id} no existe")

            # Crear modelo de dominio
            # Si no hay descripción, generar una por defecto
            description = dto.description or f"Transacción recurrente {source_account.name} → {dest_account.name}"
            
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
                next_execution_date=None  # Lo calculamos a continuación
            )

            # Calcular primera ejecución
            next_exec = self.calculate_next_execution_date(new_rule)
            new_rule = replace(new_rule, next_execution_date=next_exec)

            # Persistir
            self.uow.recurring_rules.add(new_rule)
            self.uow.commit()

            return self._to_output_dto(new_rule, source_account, dest_account)

    def update_recurring_rule(self, rule_id: UUID, dto: RecurringRuleUpdateDTO) -> RecurringRuleOutputDTO:
        """Actualiza una regla recurrente existente."""
        with self.uow:
            rule = self.uow.recurring_rules.get(rule_id)
            if not rule:
                raise ValueError(f"Regla con ID {rule_id} no encontrada")

            # Aplicar cambios
            changes = {}
            if dto.description is not None:
                changes['description'] = dto.description
            if dto.amount is not None:
                changes['amount'] = Money(dto.amount.amount, dto.amount.currency)
            if dto.tags_ids is not None:
                changes['tags_ids'] = dto.tags_ids
            if dto.end_date is not None:
                changes['end_date'] = dto.end_date
            if dto.is_active is not None:
                changes['is_active'] = dto.is_active

            updated_rule = replace(rule, **changes)

            # Recalcular next_execution_date si cambió end_date o is_active
            if 'end_date' in changes or 'is_active' in changes:
                if updated_rule.is_active and not self.is_expired(updated_rule):
                    next_exec = self.calculate_next_execution_date(updated_rule)
                    updated_rule = replace(updated_rule, next_execution_date=next_exec)

            self.uow.recurring_rules.update(updated_rule)
            self.uow.commit()

            # Obtener cuentas para el DTO
            source = self.uow.accounts.get(updated_rule.source_account_id)
            dest = self.uow.accounts.get(updated_rule.destination_account_id)

            return self._to_output_dto(updated_rule, source, dest)

    def delete_recurring_rule(self, rule_id: UUID) -> None:
        """Elimina una regla recurrente."""
        with self.uow:
            rule = self.uow.recurring_rules.get(rule_id)
            if not rule:
                raise ValueError(f"Regla con ID {rule_id} no encontrada")

            self.uow.recurring_rules.delete(rule_id)
            self.uow.commit()

    def get_recurring_rule(self, rule_id: UUID) -> RecurringRuleOutputDTO:
        """Obtiene una regla por ID."""
        with self.uow:
            rule = self.uow.recurring_rules.get(rule_id)
            if not rule:
                raise ValueError(f"Regla con ID {rule_id} no encontrada")

            source = self.uow.accounts.get(rule.source_account_id)
            dest = self.uow.accounts.get(rule.destination_account_id)

            return self._to_output_dto(rule, source, dest)

    def list_recurring_rules(self, active_only: bool = False) -> List[RecurringRuleOutputDTO]:
        """Lista todas las reglas recurrentes."""
        with self.uow:
            if active_only:
                rules = self.uow.recurring_rules.get_active_rules()
            else:
                rules = self.uow.recurring_rules.get_all()

            result = []
            for rule in rules:
                source = self.uow.accounts.get(rule.source_account_id)
                dest = self.uow.accounts.get(rule.destination_account_id)
                result.append(self._to_output_dto(rule, source, dest))

            return result

    # =========================================
    # EJECUCIÓN DE REGLAS
    # =========================================

    def execute_pending_rules(self, execution_date: datetime, transaction_service) -> List[dict]:
        """
        ORQUESTACIÓN: Ejecuta todas las reglas pendientes para una fecha.
        Coordina entre RecurringRuleService y TransactionService.

        Args:
            execution_date: Fecha para la cual ejecutar reglas
            transaction_service: Instancia de TransactionService (inyección de dependencia)

        Returns:
            Lista de diccionarios con información de las transacciones creadas
        """
        with self.uow:
            all_rules = self.uow.recurring_rules.get_all()
            rules_to_execute = [r for r in all_rules if self.should_execute_on(r, execution_date)]

            created_transactions = []

            for rule in rules_to_execute:
                try:
                    # Crear transacción automática
                    tx_dto = TransactionEntryDTO(
                        description=f"🔁 {rule.description}",
                        amount=MoneySchema(
                            amount=rule.amount.amount,
                            currency=rule.amount.currency
                        ),
                        source_account_id=rule.source_account_id,
                        destination_account_id=rule.destination_account_id,
                        date=execution_date,
                        tags_ids=rule.tags_ids
                    )

                    created_tx = transaction_service.create_transaction(tx_dto)

                    # Actualizar regla con nueva fecha de ejecución
                    updated_rule = self.mark_as_executed(rule, execution_date)
                    self.uow.recurring_rules.update(updated_rule)

                    created_transactions.append({
                        'rule_id': str(rule.id),
                        'rule_description': rule.description,
                        'transaction_id': str(created_tx.id),
                        'amount': float(created_tx.amount.amount),
                        'next_execution': updated_rule.next_execution_date.isoformat() if updated_rule.next_execution_date else None
                    })

                except Exception as e:
                    # Log error pero continuar con otras reglas
                    print(f"❌ Error ejecutando regla '{rule.description}': {str(e)}")

            self.uow.commit()
            return created_transactions

    # =========================================
    # HELPERS
    # =========================================

    def _to_output_dto(self, rule: RecurringRule, source_account, dest_account) -> RecurringRuleOutputDTO:
        """Convierte entidad de dominio a DTO de salida."""
        return RecurringRuleOutputDTO(
            id=rule.id,
            description=rule.description,
            amount=MoneySchema(amount=rule.amount.amount, currency=rule.amount.currency),
            source_account_id=rule.source_account_id,
            destination_account_id=rule.destination_account_id,
            source_account_name=source_account.name if source_account else "Cuenta desconocida",
            destination_account_name=dest_account.name if dest_account else "Cuenta desconocida",
            transaction_type=rule.transaction_type,
            tags_ids=rule.tags_ids,
            recurrence_type=rule.recurrence_type,
            frequency=rule.frequency,
            day_of_execution=rule.day_of_execution,
            interval_value=rule.interval_value,
            interval_unit=rule.interval_unit,
            start_date=rule.start_date,
            end_date=rule.end_date,
            is_active=rule.is_active,
            last_execution_date=rule.last_execution_date,
            next_execution_date=rule.next_execution_date
        )
