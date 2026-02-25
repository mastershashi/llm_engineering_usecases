import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("ENV", "dev")

def main():
    from shared.config.base import get_environment
    print("ENV", get_environment())
    from services.commerce.config import get_database_url
    print("DB", get_database_url())
    from services.commerce.infrastructure.persistence.unit_of_work import CommerceUnitOfWork
    uow = CommerceUnitOfWork(get_database_url())
    with uow.session() as s:
        from services.commerce.infrastructure.persistence.models import ProductModel
        print("Products", s.query(ProductModel).count())
    print("Commerce OK")
    from services.memory.main import app as memory_app
    from services.agent.main import app as agent_app
    from services.orchestration.main import app as orch_app
    from services.gateway.main import app as gw_app
    print("All services import OK")

if __name__ == "__main__":
    main()
