from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import Token, UserCreate, UserPublic


class UsuarioService:
    def __init__(self, uow) -> None:
        self.uow = uow

    def register(self, user_in: UserCreate) -> UserPublic:
        email_normalizado = user_in.email.strip().lower()
        username_limpio = user_in.username.strip()

        if self.uow.usuarios.get_by_username(username_limpio):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El nombre de usuario ya está registrado",
            )
        if self.uow.usuarios.get_by_email(email_normalizado):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El correo electrónico ya está registrado",
            )

        nuevo_usuario = Usuario(
            username=username_limpio,
            full_name=user_in.full_name.strip(),
            email=email_normalizado,
            hashed_password=hash_password(user_in.password),
            role="user",
            disabled=False,
            created_at=datetime.now(UTC),
        )

        self.uow.usuarios.add(nuevo_usuario)
        return UserPublic.model_validate(nuevo_usuario)

    def authenticate(self, username_or_email: str, password: str) -> Token:
        identificador = username_or_email.strip()
        user = self.uow.usuarios.get_by_username(identificador) or self.uow.usuarios.get_by_email(
            identificador.lower()
        )

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos",
            )
        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cuenta de usuario está desactivada",
            )

        access_token = create_access_token(data={"sub": user.username, "role": user.role})
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def list_all_users(self) -> list[UserPublic]:
        usuarios = self.uow.usuarios.get_all()
        return [UserPublic.model_validate(u) for u in usuarios]

    def activar_usuario(self, usuario_id: int) -> UserPublic:
        usuario = self.uow.usuarios.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        usuario.disabled = False
        self.uow.usuarios.add(usuario)
        return UserPublic.model_validate(usuario)

    def desactivar_usuario(self, usuario_id: int, admin_id_actual: int) -> UserPublic:
        if usuario_id == admin_id_actual:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El administrador no puede desactivarse a sí mismo",
            )
        usuario = self.uow.usuarios.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        usuario.disabled = True
        self.uow.usuarios.add(usuario)
        return UserPublic.model_validate(usuario)
