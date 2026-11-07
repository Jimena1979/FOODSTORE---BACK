# app/core/config.py
from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuración cargada desde variables de entorno o archivo .env.

    Acepta las variables individuales de Postgres y construye DATABASE_URL
    automáticamente con @computed_field, o usa DATABASE_URL directamente
    si se provee en el entorno.

    Orden de prioridad (pydantic-settings):
      1. Variables de entorno del sistema
      2. Archivo .env
      3. Defaults declarados en la clase
    """

    """
    Configuración cargada desde variables de entorno o archivo .env.
    """

    postgres_user: str = "postgres"
    postgres_password: str = "password"
    postgres_db: str = "foodstore_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Seguridad y JWT
    SECRET_KEY: str = "cambiar-esta-clave-de-al-menos-32-caracteres"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS (Requerido por la consigna para conectar el frontend)
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()