
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated

from pydantic import StringConstraints
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.pedidos.models import Pedido


class UsuarioBase(SQLModel):
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)] = Field(
        index=True, unique=True, nullable=False
    )
    full_name: Annotated[str, StringConstraints(min_length=2, max_length=150)] = Field(
        nullable=False
    )
    email: Annotated[str, StringConstraints(min_length=5, max_length=255)] = Field(
        index=True, unique=True, nullable=False
    )
    role: str = Field(default="user", nullable=False)  # "user" o "admin"
    disabled: bool = Field(default=False, nullable=False)  # Baja lógica con disabled = true


class Usuario(UsuarioBase, table=True):
    __tablename__ = "usuario"

    id: int | None = Field(default=None, primary_key=True)  # Clave primaria autoincremental
    hashed_password: str = Field(nullable=False)  # Contraseña almacenada con hash bcrypt
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)

    # Relación 1:N exacta requerida por el UML (un usuario realiza n pedidos)
    pedidos: list["Pedido"] = Relationship(back_populates="usuario")