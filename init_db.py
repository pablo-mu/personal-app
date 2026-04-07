#!/usr/bin/env python
"""
Script de inicialización de la base de datos.

Uso:
    # Solo crear tablas vacías
    python init_db.py

    # Crear tablas + datos de ejemplo (cuentas, categorías, etiquetas)
    python init_db.py --seed

    # Borrar todo y volver a crear desde cero (¡DESTRUCTIVO!)
    python init_db.py --reset

    # Borrar + crear + datos de ejemplo
    python init_db.py --reset --seed
"""

import argparse
import sys
import os
from decimal import Decimal
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Importaciones ────────────────────────────────────────────────────────────
from src.config import settings
from src.infrastructure.persistence.db import engine, Base
from src.infrastructure.persistence.models import (
    AccountModel,
    TransactionModel,
    TagModel,
    TransactionEntryModel,
    RecurringRuleModel,
)
from src.infrastructure.persistence.uow import SQLAlchemyUnitOfWork
from src.application.services import AccountService, TagService
from src.application.dtos import AccountCreateDTO, TagDTO, MoneySchema
from src.domain.models import AccountType


# ─────────────────────────────────────────────────────────────────────────────
# Datos de ejemplo
# ─────────────────────────────────────────────────────────────────────────────

SEED_ACCOUNTS = [
    # ── Activos ──────────────────────────────────────────────────────────────
    dict(name="Cuenta Corriente",  type=AccountType.ASSET,     initial_balance=0.00,    currency="EUR"),
    dict(name="Cuenta Ahorro",     type=AccountType.ASSET,     initial_balance=0.00,    currency="EUR"),
    dict(name="Efectivo",          type=AccountType.ASSET,     initial_balance=0.00,    currency="EUR"),
    # ── Pasivos ───────────────────────────────────────────────────────────────
    dict(name="Tarjeta Crédito",   type=AccountType.LIABILITY, initial_balance=0.00,    currency="EUR"),
    # ── Ingresos ─────────────────────────────────────────────────────────────
    dict(name="Salario",           type=AccountType.INCOME,    initial_balance=0.00,    currency="EUR"),
    dict(name="Freelance",         type=AccountType.INCOME,    initial_balance=0.00,    currency="EUR"),
    dict(name="Otros Ingresos",    type=AccountType.INCOME,    initial_balance=0.00,    currency="EUR"),
    # ── Gastos ────────────────────────────────────────────────────────────────
    dict(name="Alimentación",      type=AccountType.EXPENSE,   initial_balance=0.00,    currency="EUR"),
    dict(name="Transporte",        type=AccountType.EXPENSE,   initial_balance=0.00,    currency="EUR"),
    dict(name="Vivienda",          type=AccountType.EXPENSE,   initial_balance=0.00,    currency="EUR"),
    dict(name="Salud",             type=AccountType.EXPENSE,   initial_balance=0.00,    currency="EUR"),
    dict(name="Ocio y Cultura",    type=AccountType.EXPENSE,   initial_balance=0.00,    currency="EUR"),
    dict(name="Ropa y Calzado",    type=AccountType.EXPENSE,   initial_balance=0.00,    currency="EUR"),
    dict(name="Tecnología",        type=AccountType.EXPENSE,   initial_balance=0.00,    currency="EUR"),
    dict(name="Suscripciones",     type=AccountType.EXPENSE,   initial_balance=0.00,    currency="EUR"),
    dict(name="Restaurantes",      type=AccountType.EXPENSE,   initial_balance=0.00,    currency="EUR"),
    dict(name="Viajes",            type=AccountType.EXPENSE,   initial_balance=0.00,    currency="EUR"),
    dict(name="Educación",         type=AccountType.EXPENSE,   initial_balance=0.00,    currency="EUR"),
    dict(name="Seguros",           type=AccountType.EXPENSE,   initial_balance=0.00,    currency="EUR"),
    dict(name="Gastos Varios",     type=AccountType.EXPENSE,   initial_balance=0.00,    currency="EUR"),
]

SEED_TAGS = [
    dict(name="supermercado",   color="#27ae60"),
    dict(name="online",         color="#2980b9"),
    dict(name="recurrente",     color="#8e44ad"),
    dict(name="urgente",        color="#e74c3c"),
    dict(name="trabajo",        color="#f39c12"),
    dict(name="familia",        color="#16a085"),
    dict(name="deducible",      color="#d35400"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Operaciones
# ─────────────────────────────────────────────────────────────────────────────

def drop_tables():
    print("🗑️  Eliminando tablas existentes...")
    Base.metadata.drop_all(bind=engine)
    print("   OK")


def create_tables():
    print("🛠️  Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("   OK — tablas creadas:")
    for table in Base.metadata.sorted_tables:
        print(f"      • {table.name}")


def seed_data():
    print()
    print("🌱 Insertando datos de ejemplo...")

    uow = SQLAlchemyUnitOfWork()
    account_svc = AccountService(uow)
    tag_svc     = TagService(uow)

    # Etiquetas
    print("   Etiquetas:")
    created_tags = 0
    for t in SEED_TAGS:
        try:
            tag_svc.create_tag(TagDTO(name=t["name"], color=t["color"]))
            print(f"      ✓ {t['name']}")
            created_tags += 1
        except Exception as e:
            print(f"      ⚠  {t['name']} — {e}")

    # Cuentas
    print("   Cuentas:")
    created_accs = 0
    for a in SEED_ACCOUNTS:
        try:
            account_svc.create_account(AccountCreateDTO(
                name=a["name"],
                type=a["type"],
                initial_balance=MoneySchema(amount=Decimal(str(a["initial_balance"])), currency=a["currency"]),
            ))
            print(f"      ✓ [{a['type'].value:10}] {a['name']}")
            created_accs += 1
        except Exception as e:
            print(f"      ⚠  {a['name']} — {e}")

    print()
    print(f"   Creados: {created_tags} etiquetas, {created_accs} cuentas.")


def run_migration():
    """
    Añade columnas nuevas a tablas existentes sin perder datos.
    Solo necesario si actualizas desde una versión anterior a este script.
    """
    print()
    print("🔄 Ejecutando migraciones de esquema...")
    from sqlalchemy import text, inspect

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if "accounts" not in existing_tables:
        print("   No hay tablas previas, nada que migrar.")
        return

    with engine.connect() as conn:
        existing_cols = {c["name"] for c in inspector.get_columns("accounts")}

        if "current_balance" not in existing_cols:
            conn.execute(text(
                "ALTER TABLE accounts ADD COLUMN current_balance NUMERIC(15,2) DEFAULT 0.00"
            ))
            print("   ✓ Columna 'current_balance' añadida.")

        if "current_balance_currency" not in existing_cols:
            conn.execute(text(
                "ALTER TABLE accounts ADD COLUMN current_balance_currency VARCHAR(3) DEFAULT 'EUR'"
            ))
            print("   ✓ Columna 'current_balance_currency' añadida.")

        conn.commit()

    # Recalcular saldos si hacía falta migrar
    if "current_balance" not in existing_cols:
        print("   Recalculando saldos actuales...")
        from sqlalchemy.orm import Session
        from sqlalchemy import func as sqlfunc

        with Session(engine) as session:
            accounts = session.query(AccountModel).all()
            for acc in accounts:
                total = (
                    session.query(sqlfunc.sum(TransactionEntryModel.amount))
                    .filter(TransactionEntryModel.account_id == acc.id)
                    .scalar()
                ) or Decimal("0.00")
                acc.current_balance          = Decimal(str(acc.initial_balance)) + Decimal(str(total))
                acc.current_balance_currency = acc.initial_balance_currency
            session.commit()
        print(f"   ✓ Saldos recalculados para {len(accounts)} cuentas.")

    print("   Migraciones completadas.")


# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Inicialización y mantenimiento de la base de datos de Mi Finanza."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Elimina TODAS las tablas antes de crearlas de nuevo (¡DESTRUCTIVO!).",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Inserta cuentas y etiquetas de ejemplo tras crear las tablas.",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Solo ejecuta migraciones de esquema sin recrear tablas.",
    )
    args = parser.parse_args()

    print(f"📦 Base de datos: {settings.DATABASE_URL}")
    print()

    if args.migrate:
        run_migration()
        return

    if args.reset:
        confirm = input(
            "⚠️  --reset borrará TODOS los datos. Escribe 'SI' para confirmar: "
        )
        if confirm.strip().upper() != "SI":
            print("Cancelado.")
            sys.exit(0)
        drop_tables()
        print()

    create_tables()

    # Migraciones en caso de que existieran tablas con esquema antiguo
    if not args.reset:
        run_migration()

    if args.seed:
        seed_data()

    print()
    print("✅ Base de datos lista.")
    print()
    print("  Para lanzar la aplicación:")
    print("    python main.py")
    print()
    print("  Endpoints disponibles una vez arrancada:")
    print(f"    API REST  →  http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print(f"    Dash UI   →  http://{settings.DASH_HOST}:{settings.DASH_PORT}/")


if __name__ == "__main__":
    main()