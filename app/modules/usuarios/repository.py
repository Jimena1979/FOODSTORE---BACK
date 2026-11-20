from sqlmodel import func, select

from app.core.base_repository import BaseRepository
from app.modules.usuarios.models import Usuario


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, session) -> None:
        super().__init__(session, Usuario)

    def get_by_username(self, username: str) -> Usuario | None:
        normalizado = username.strip().lower()
        statement = select(self.model).where(
            func.lower(self.model.username) == normalizado
        )
        return self.session.exec(statement).first()

    def get_by_email(self, email: str) -> Usuario | None:
        normalizado = email.strip().lower()
        statement = select(self.model).where(
            func.lower(self.model.email) == normalizado
        )
        return self.session.exec(statement).first()