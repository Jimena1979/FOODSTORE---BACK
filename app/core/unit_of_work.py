# app/core/unit_of_work.py
from collections.abc import Iterator
from typing import Self

from sqlmodel import Session

from app.core.database import SessionLocal
from app.modules.categorias.repository import CategoriaRepository
from app.modules.pedidos.repository import PedidoRepository
from app.modules.productos.repository import ProductoRepository
from app.modules.usuarios.repository import UsuarioRepository


class UnitOfWork:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session if session else SessionLocal()
        
        self.categorias = CategoriaRepository(self._session)
        self.productos = ProductoRepository(self._session)
        self.pedidos = PedidoRepository(self._session)
        self.usuarios = UsuarioRepository(self._session)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self._session.commit()
        else:
            self._session.rollback()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()


def get_uow() -> Iterator[UnitOfWork]:
    with UnitOfWork() as uow:
        yield uow