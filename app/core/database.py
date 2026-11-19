# app/core/database.py
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

# Configuración del motor. 
# Si se usa SQLite en el .env, se requiere connect_args={"check_same_thread": False}
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)

# Fábrica de sesiones requerida por el UnitOfWork
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
)


def create_db_and_tables() -> None:
    from app.modules.categorias.models import Categoria  # noqa: F401
    from app.modules.pedidos.models import DetallePedido, Pedido  # noqa: F401
    from app.modules.productos.models import Producto  # noqa: F401
    from app.modules.usuarios.models import Usuario  # noqa: F401
    """Crea todas las tablas definidas con SQLModel al iniciar la app."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Dependencia FastAPI que provee una Session por request.
    Usada exclusivamente por el UnitOfWork.
    """
    with Session(engine) as session:
        yield session