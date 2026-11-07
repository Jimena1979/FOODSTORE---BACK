
from datetime import datetime
from typing import Annotated

from pydantic import EmailStr, StringConstraints, field_validator
from sqlmodel import SQLModel


class UserCreate(SQLModel):
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)]
    full_name: Annotated[str, StringConstraints(min_length=2, max_length=150)]
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=8, max_length=100)]

    @field_validator("username", "full_name")
    @classmethod
    def validar_textos(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío ni contener solo espacios")
        return value

    @field_validator("email")
    @classmethod
    def validar_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("El email no puede estar vacío")
        return value



class UserPublic(SQLModel):
    id: int
    username: str
    full_name: str
    email: str
    role: str
    disabled: bool
    created_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int