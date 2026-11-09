
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import create_db_and_tables

# Importación de todos los routers de la aplicación
from app.modules.categorias.router import router as categoria_router
from app.modules.pedidos.router import router as pedido_router
from app.modules.productos.router import router as producto_router
from app.modules.usuarios.router import router as usuario_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que se ejecuta al arrancar la aplicación (crea las tablas)
    create_db_and_tables()
    yield
    # Código al apagar la aplicación (si fuera necesario)


app = FastAPI(
    title="Food Store Backend",
    version="2.0.0",
    description="Backend modular con FastAPI, SQLModel y PostgreSQL.",
    lifespan=lifespan,
)

# --- MANEJADOR PERSONALIZADO PARA ERRORES 422 (Punto 4)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    mensajes_error = []
    
    for error in exc.errors():
        # Obtenemos el campo o ruta donde ocurrió el error (ej: body -> nombre)
        ubicacion = error.get("loc", [])
        # Filtramos 'body' o 'query' para quedarnos con el nombre exacto del campo
        campo = " -> ".join(str(loc) for loc in ubicacion if loc != "body")
        
        # Obtenemos el mensaje descriptivo del error de Pydantic
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

# Configuración de CORS para permitir peticiones desde el Front-End (ej: React/Vite en puerto 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],                    # Permite todos los métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],                    # Permite todas las cabeceras
)

# Inclusión de los routers de la aplicación
app.include_router(producto_router)
app.include_router(categoria_router)
app.include_router(pedido_router)
app.include_router(usuario_router)

@app.get("/")
def root():
    return {"message": "API de Food Store funcionando correctamente con PostgreSQL"}