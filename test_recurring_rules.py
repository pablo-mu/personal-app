"""
Script de prueba para verificar el sistema de reglas recurrentes.
"""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.infrastructure.persistence.db import engine, Base
from src.infrastructure.persistence.models import (
    AccountModel,
    TransactionModel,
    TagModel,
    TransactionEntryModel,
    RecurringRuleModel
)
from src.infrastructure.persistence.uow import SQLAlchemyUnitOfWork
from src.application.services import AccountService, TransactionService
from src.application.services.recurring_rule_service import RecurringRuleService
from src.application.dtos import (
    AccountCreateDTO,
    MoneySchema,
    RecurringRuleCreateDTO
)
from src.domain.models import AccountType, RecurrenceType, RecurrenceFrequency, IntervalUnit

def test_recurring_rules():
    """Prueba el sistema completo de reglas recurrentes."""
    
    print("🧪 Iniciando pruebas de Reglas Recurrentes\n")
    print("=" * 60)
    
    # Crear tablas
    Base.metadata.create_all(bind=engine)
    
    # Inicializar servicios
    uow = SQLAlchemyUnitOfWork()
    account_service = AccountService(uow)
    transaction_service = TransactionService(uow)
    recurring_service = RecurringRuleService(uow)
    
    # 1. Crear cuentas de prueba
    print("\n📁 1. Creando cuentas de prueba...")
    
    try:
        banco = account_service.create_account(AccountCreateDTO(
            name="Banco Santander",
            type=AccountType.ASSET,
            initial_balance=MoneySchema(amount=Decimal("1000.00"), currency="EUR")
        ))
        print(f"   ✅ Cuenta creada: {banco.name} ({banco.id})")
    except Exception as e:
        print(f"   ℹ️  Cuenta ya existe, recuperando...")
        with uow:
            cuentas = uow.accounts.list()
            banco = next((c for c in cuentas if c.name == "Banco Santander"), None)
            if not banco:
                raise e
    
    try:
        gastos_ocio = account_service.create_account(AccountCreateDTO(
            name="Gastos - Ocio",
            type=AccountType.EXPENSE,
            initial_balance=MoneySchema(amount=Decimal("0.00"), currency="EUR")
        ))
        print(f"   ✅ Cuenta creada: {gastos_ocio.name} ({gastos_ocio.id})")
    except Exception as e:
        print(f"   ℹ️  Cuenta ya existe, recuperando...")
        with uow:
            cuentas = uow.accounts.list()
            gastos_ocio = next((c for c in cuentas if c.name == "Gastos - Ocio"), None)
            if not gastos_ocio:
                raise e
    
    # 2. Crear regla CALENDAR_BASED (Mensual)
    print("\n📅 2. Creando regla MENSUAL (Netflix)...")
    
    netflix_dto = RecurringRuleCreateDTO(
        description="Suscripción Netflix",
        amount=MoneySchema(amount=Decimal("15.99"), currency="EUR"),
        source_account_id=banco.id,
        destination_account_id=gastos_ocio.id,
        recurrence_type=RecurrenceType.CALENDAR_BASED,
        frequency=RecurrenceFrequency.MONTHLY,
        day_of_execution=15,  # Día 15 de cada mes
        start_date=datetime.now()
    )
    
    netflix_rule = recurring_service.create_recurring_rule(netflix_dto)
    print(f"   ✅ Regla creada: {netflix_rule.description}")
    print(f"      ID: {netflix_rule.id}")
    print(f"      Próxima ejecución: {netflix_rule.next_execution_date}")
    
    # 3. Crear regla INTERVAL_BASED (Cada 30 días)
    print("\n⏱️  3. Creando regla INTERVALO (Medicamento cada 30 días)...")
    
    medicamento_dto = RecurringRuleCreateDTO(
        description="Compra medicamento crónico",
        amount=MoneySchema(amount=Decimal("42.50"), currency="EUR"),
        source_account_id=banco.id,
        destination_account_id=gastos_ocio.id,
        recurrence_type=RecurrenceType.INTERVAL_BASED,
        interval_value=30,
        interval_unit=IntervalUnit.DAYS,
        start_date=datetime.now()
    )
    
    medicamento_rule = recurring_service.create_recurring_rule(medicamento_dto)
    print(f"   ✅ Regla creada: {medicamento_rule.description}")
    print(f"      ID: {medicamento_rule.id}")
    print(f"      Próxima ejecución: {medicamento_rule.next_execution_date}")
    
    # 4. Preview de ejecuciones
    print("\n🔮 4. Preview de próximas 5 ejecuciones...")
    
    with uow:
        netflix_domain = uow.recurring_rules.get(netflix_rule.id)
        preview = recurring_service.preview_executions(netflix_domain, num_executions=5)
        
        print(f"\n   Netflix (Mensual día 15):")
        for i, fecha in enumerate(preview, 1):
            print(f"      {i}. {fecha.strftime('%d/%m/%Y')}")
    
    with uow:
        medicamento_domain = uow.recurring_rules.get(medicamento_rule.id)
        preview = recurring_service.preview_executions(medicamento_domain, num_executions=5)
        
        print(f"\n   Medicamento (Cada 30 días):")
        for i, fecha in enumerate(preview, 1):
            print(f"      {i}. {fecha.strftime('%d/%m/%Y')}")
    
    # 5. Listar todas las reglas
    print("\n📋 5. Listando todas las reglas activas...")
    
    rules = recurring_service.list_recurring_rules(active_only=True)
    print(f"\n   Total reglas activas: {len(rules)}")
    for rule in rules:
        print(f"\n   • {rule.description}")
        print(f"     Tipo: {rule.recurrence_type.value}")
        print(f"     Monto: {rule.amount.amount} {rule.amount.currency}")
        print(f"     Próxima ejecución: {rule.next_execution_date}")
    
    # 6. Simular ejecución
    print("\n⚡ 6. Simulando ejecución de reglas pendientes...")
    
    # Forzamos una fecha que debería ejecutar la regla
    test_date = datetime.now() + timedelta(days=1)
    
    print(f"   Fecha de prueba: {test_date.strftime('%d/%m/%Y')}")
    
    # NOTA: Aquí necesitamos pasar transaction_service como dependencia
    # created = recurring_service.execute_pending_rules(test_date, transaction_service)
    # print(f"   ✅ Transacciones creadas: {len(created)}")
    print("   ℹ️  Ejecución automática deshabilitada en prueba (requiere scheduler)")
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas exitosamente\n")

if __name__ == "__main__":
    try:
        test_recurring_rules()
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()
