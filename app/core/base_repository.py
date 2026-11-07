from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlmodel import Session, SQLModel, select

ModelT = TypeVar("ModelT", bound=SQLModel)

class BaseRepository(Generic[ModelT]):
    """
    Repositorio genérico que implementa operaciones CRUD básicas
    para cualquier modelo basado en SQLModel.
    """
    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def get_by_id(self, record_id: int) -> ModelT | None:
        instance = self.session.get(self.model, record_id)
        if instance:
            self.session.expunge(instance)
        return instance

    def get_all(self, offset: int = 0, limit: int = 20) -> Sequence[ModelT]:
        items = list(self.session.exec(
            select(self.model).offset(offset).limit(limit)
        ).all())
        
        for item in items:
            self.session.expunge(item)
            
        return items

    def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        self.session.flush()  # obtiene el ID sin hacer commit
        self.session.refresh(instance)
        self.session.expunge(instance)  # <-- ¡CLAVE! Desvincula el objeto de la sesión para que Pydantic lo lea sin errores
        return instance

    def delete(self, instance: ModelT) -> None:
        self.session.delete(instance)
        self.session.flush()