import sys
import os
from decimal import Decimal

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.infrastructure.persistence.uow import SQLAlchemyUnitOfWork
from src.application.services import AccountService
from src.infrastructure.persistence.db import engine, Base

def test_list_accounts():
    print("Testing list_accounts...")
    try:
        uow = SQLAlchemyUnitOfWork()
        service = AccountService(uow)
        
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
        
        accounts = service.list_accounts()
        print(f"Successfully retrieved {len(accounts)} accounts.")
        for acc in accounts:
            print(f" - {acc.name}: {acc.initial_balance}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_list_accounts()
