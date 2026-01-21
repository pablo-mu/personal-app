"""
Script para inicializar la base de datos con datos de prueba.
Elimina la DB existente y crea una nueva con el esquema actualizado.
"""
import os
import random
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.infrastructure.persistence.db import Base, engine
from src.infrastructure.persistence.models import (
    AccountModel, TagModel, TransactionModel, TransactionEntryModel, transaction_tags
)
from sqlalchemy.orm import Session

# Colores para tags
TAG_COLORS = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6",
    "#1abc9c", "#e67e22", "#34495e", "#16a085", "#c0392b",
    "#d35400", "#8e44ad", "#2980b9", "#27ae60", "#f1c40f"
]

# Nombres de tags comunes
TAG_NAMES = [
    "Marruecos", "Vacaciones", "Urgente", "Ocio", "Salud",
    "Familia", "Trabajo", "Educación", "Hogar", "Transporte",
    "Regalo", "Inversión", "Ahorro", "Subscripción", "Navidad"
]

def recreate_database():
    """Elimina y recrea todas las tablas."""
    print("🗑️  Eliminando tablas existentes...")
    Base.metadata.drop_all(bind=engine)
    
    print("🏗️  Creando nuevas tablas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Esquema de base de datos creado")

def create_sample_data():
    """Crea datos de prueba."""
    session = Session(engine)
    
    try:
        print("\n📝 Creando datos de prueba...\n")
        
        # --- CUENTAS ---
        print("💳 Creando cuentas...")
        accounts = {
            "efectivo": AccountModel(
                id=str(uuid4()),
                name="Efectivo",
                type="ASSET",
                initial_balance=Decimal("500.00"),
                initial_balance_currency="EUR",
                is_active=1
            ),
            "banco": AccountModel(
                id=str(uuid4()),
                name="Cuenta Corriente",
                type="ASSET",
                initial_balance=Decimal("2500.00"),
                initial_balance_currency="EUR",
                is_active=1,
                account_number="ES12 3456 7890 1234 5678 9012"
            ),
            "ahorros": AccountModel(
                id=str(uuid4()),
                name="Cuenta Ahorro",
                type="ASSET",
                initial_balance=Decimal("5000.00"),
                initial_balance_currency="EUR",
                is_active=1
            ),
            "tarjeta": AccountModel(
                id=str(uuid4()),
                name="Tarjeta Crédito",
                type="LIABILITY",
                initial_balance=Decimal("0.00"),
                initial_balance_currency="EUR",
                is_active=1
            ),
            "salario": AccountModel(
                id=str(uuid4()),
                name="Salario",
                type="INCOME",
                initial_balance=Decimal("0.00"),
                initial_balance_currency="EUR",
                is_active=1
            ),
            "alquiler": AccountModel(
                id=str(uuid4()),
                name="Alquiler",
                type="EXPENSE",
                initial_balance=Decimal("0.00"),
                initial_balance_currency="EUR",
                is_active=1
            ),
            "comida": AccountModel(
                id=str(uuid4()),
                name="Comida",
                type="EXPENSE",
                initial_balance=Decimal("0.00"),
                initial_balance_currency="EUR",
                is_active=1
            ),
            "transporte": AccountModel(
                id=str(uuid4()),
                name="Transporte",
                type="EXPENSE",
                initial_balance=Decimal("0.00"),
                initial_balance_currency="EUR",
                is_active=1
            ),
            "ocio": AccountModel(
                id=str(uuid4()),
                name="Ocio",
                type="EXPENSE",
                initial_balance=Decimal("0.00"),
                initial_balance_currency="EUR",
                is_active=1
            ),
        }
        
        session.add_all(accounts.values())
        session.commit()
        print(f"   ✓ {len(accounts)} cuentas creadas")
        
        # --- TAGS ---
        print("🏷️  Creando etiquetas...")
        tags = []
        for i, name in enumerate(TAG_NAMES[:10]):  # Crear 10 tags
            tag = TagModel(
                id=str(uuid4()),
                name=name,
                color=TAG_COLORS[i % len(TAG_COLORS)]
            )
            tags.append(tag)
            session.add(tag)
        
        session.commit()
        print(f"   ✓ {len(tags)} etiquetas creadas")
        
        # --- TRANSACCIONES ---
        print("💰 Creando transacciones...")
        transactions_created = 0
        
        # Transacción 1: Cobro salario
        t1 = TransactionModel(
            id=str(uuid4()),
            date=datetime.now() - timedelta(days=30),
            description="Nómina enero"
        )
        session.add(t1)
        session.flush()
        
        # Entradas de la transacción (doble partida)
        session.add(TransactionEntryModel(
            transaction_id=t1.id,
            account_id=accounts["banco"].id,
            amount=Decimal("2500.00"),
            currency="EUR"
        ))
        session.add(TransactionEntryModel(
            transaction_id=t1.id,
            account_id=accounts["salario"].id,
            amount=Decimal("-2500.00"),
            currency="EUR"
        ))
        t1.tags.append(tags[6])  # Tag "Trabajo"
        transactions_created += 1
        
        # Transacción 2: Pago alquiler
        t2 = TransactionModel(
            id=str(uuid4()),
            date=datetime.now() - timedelta(days=28),
            description="Alquiler enero"
        )
        session.add(t2)
        session.flush()
        
        session.add(TransactionEntryModel(
            transaction_id=t2.id,
            account_id=accounts["banco"].id,
            amount=Decimal("-800.00"),
            currency="EUR"
        ))
        session.add(TransactionEntryModel(
            transaction_id=t2.id,
            account_id=accounts["alquiler"].id,
            amount=Decimal("800.00"),
            currency="EUR"
        ))
        t2.tags.append(tags[8])  # Tag "Hogar"
        transactions_created += 1
        
        # Transacción 3: Supermercado
        t3 = TransactionModel(
            id=str(uuid4()),
            date=datetime.now() - timedelta(days=5),
            description="Compra Mercadona"
        )
        session.add(t3)
        session.flush()
        
        session.add(TransactionEntryModel(
            transaction_id=t3.id,
            account_id=accounts["banco"].id,
            amount=Decimal("-125.50"),
            currency="EUR"
        ))
        session.add(TransactionEntryModel(
            transaction_id=t3.id,
            account_id=accounts["comida"].id,
            amount=Decimal("125.50"),
            currency="EUR"
        ))
        t3.tags.append(tags[8])  # Tag "Hogar"
        transactions_created += 1
        
        # Transacción 4: Metro
        t4 = TransactionModel(
            id=str(uuid4()),
            date=datetime.now() - timedelta(days=3),
            description="Bono metro"
        )
        session.add(t4)
        session.flush()
        
        session.add(TransactionEntryModel(
            transaction_id=t4.id,
            account_id=accounts["efectivo"].id,
            amount=Decimal("-20.00"),
            currency="EUR"
        ))
        session.add(TransactionEntryModel(
            transaction_id=t4.id,
            account_id=accounts["transporte"].id,
            amount=Decimal("20.00"),
            currency="EUR"
        ))
        t4.tags.append(tags[9])  # Tag "Transporte"
        transactions_created += 1
        
        # Transacción 5: Cine
        t5 = TransactionModel(
            id=str(uuid4()),
            date=datetime.now() - timedelta(days=2),
            description="Entradas cine"
        )
        session.add(t5)
        session.flush()
        
        session.add(TransactionEntryModel(
            transaction_id=t5.id,
            account_id=accounts["tarjeta"].id,
            amount=Decimal("18.00"),
            currency="EUR"
        ))
        session.add(TransactionEntryModel(
            transaction_id=t5.id,
            account_id=accounts["ocio"].id,
            amount=Decimal("18.00"),
            currency="EUR"
        ))
        t5.tags.append(tags[3])  # Tag "Ocio"
        transactions_created += 1
        
        # Transacción 6: Viaje a Marruecos
        t6 = TransactionModel(
            id=str(uuid4()),
            date=datetime.now() - timedelta(days=15),
            description="Hotel Marrakech"
        )
        session.add(t6)
        session.flush()
        
        session.add(TransactionEntryModel(
            transaction_id=t6.id,
            account_id=accounts["ahorros"].id,
            amount=Decimal("-450.00"),
            currency="EUR"
        ))
        session.add(TransactionEntryModel(
            transaction_id=t6.id,
            account_id=accounts["ocio"].id,
            amount=Decimal("450.00"),
            currency="EUR"
        ))
        t6.tags.append(tags[0])  # Tag "Marruecos"
        t6.tags.append(tags[1])  # Tag "Vacaciones"
        transactions_created += 1
        
        # Transacción 7: Restaurante en Marruecos
        t7 = TransactionModel(
            id=str(uuid4()),
            date=datetime.now() - timedelta(days=14),
            description="Restaurante Fez"
        )
        session.add(t7)
        session.flush()
        
        session.add(TransactionEntryModel(
            transaction_id=t7.id,
            account_id=accounts["efectivo"].id,
            amount=Decimal("-85.00"),
            currency="EUR"
        ))
        session.add(TransactionEntryModel(
            transaction_id=t7.id,
            account_id=accounts["comida"].id,
            amount=Decimal("85.00"),
            currency="EUR"
        ))
        t7.tags.append(tags[0])  # Tag "Marruecos"
        t7.tags.append(tags[1])  # Tag "Vacaciones"
        transactions_created += 1
        
        session.commit()
        print(f"   ✓ {transactions_created} transacciones creadas")
        
        print("\n✅ Base de datos inicializada correctamente\n")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error al crear datos de prueba: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 50)
    print("  INICIALIZACIÓN DE BASE DE DATOS")
    print("=" * 50)
    
    recreate_database()
    create_sample_data()
    
    print("=" * 50)
    print("  ¡LISTO!")
    print("=" * 50)
