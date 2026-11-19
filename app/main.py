from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.modules.categorias.router import router as categoria_router
from app.modules.pedidos.router import router as pedido_router
from app.modules.productos.router import router as producto_router
from app.modules.usuarios.router import router as usuario_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Food Store Backend",
    version="2.0.0",
    description="Backend modular con FastAPI, SQLModel y PostgreSQL.",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    mensajes_error = []

    for error in exc.errors():
        ubicacion = error.get("loc", [])
        campo = " -> ".join(str(loc) for loc in ubicacion if loc != "body")
        mensaje_original = error.get("msg", "Error de validación")

        if campo:
            mensajes_error.append(f"El campo '{campo}' falló: {mensaje_original}")
        else:
            mensajes_error.append(mensaje_original)

    detalle_personalizado = " | ".join(mensajes_error)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detalle_personalizado},
    )


origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
allowed_origins = list(dict.fromkeys(origin for origin in origins if origin))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(producto_router, prefix="/api/v1")
app.include_router(categoria_router, prefix="/api/v1")
app.include_router(pedido_router, prefix="/api/v1")
app.include_router(usuario_router)


@app.get("/")
def root():
    return {"message": "API de Food Store funcionando correctamente"}