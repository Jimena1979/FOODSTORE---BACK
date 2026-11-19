"""
Script idempotente de inicialización para poblar la base de datos:
- Usuario administrador (admin / Admin1234!, role="admin")
- Al menos 3 categorías activas
- Al menos 8 productos activos con stock e imagen_url

Ejecución:
    python -m app.db.seed
"""

from sqlmodel import Session, select

from app.core.database import create_db_and_tables, engine
from app.core.security import hash_password
from app.modules.categorias.models import Categoria
from app.modules.pedidos.models import DetallePedido, Pedido  # noqa: F401
from app.modules.productos.models import Producto
from app.modules.usuarios.models import Usuario


def seed_data() -> None:
    create_db_and_tables()

    with Session(engine) as session:
        print("Iniciando seed de Food Store...")

        # 1. Usuario administrador (idempotente)
        admin_username = "admin"
        admin_email = "admin@foodstore.com"
        admin_user = session.exec(
            select(Usuario).where(
                (Usuario.username == admin_username) | (Usuario.email == admin_email)
            )
        ).first()

        if not admin_user:
            admin_user = Usuario(
                username=admin_username,
                full_name="Administrador Food Store",
                email=admin_email,
                role="admin",
                disabled=False,
                hashed_password=hash_password("Admin1234!"),
            )
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            print("  - Admin creado: admin / Admin1234!")
        else:
            if admin_user.role != "admin" or admin_user.disabled:
                admin_user.role = "admin"
                admin_user.disabled = False
                session.add(admin_user)
                session.commit()
            print("  - Admin ya existente.")

        # 2. Categorías (al menos 3, idempotentes)
        categorias_data = [
            {
                "nombre": "Pizzas",
                "descripcion": "Pizzas artesanales al molde y a la piedra",
                "activo": True,
            },
            {
                "nombre": "Hamburguesas",
                "descripcion": "Hamburguesas caseras con papas y aderezos",
                "activo": True,
            },
            {
                "nombre": "Bebidas",
                "descripcion": "Gaseosas, aguas y bebidas frías",
                "activo": True,
            },
            {
                "nombre": "Postres",
                "descripcion": "Opciones dulces para acompañar tu pedido",
                "activo": True,
            },
        ]

        categorias_por_nombre: dict[str, Categoria] = {}
        for cat_data in categorias_data:
            existente = session.exec(
                select(Categoria).where(Categoria.nombre == cat_data["nombre"])
            ).first()
            if not existente:
                existente = Categoria(**cat_data)
                session.add(existente)
                session.commit()
                session.refresh(existente)
                print(f"  - Categoría creada: {existente.nombre}")
            else:
                print(f"  - Categoría ya existente: {existente.nombre}")
            categorias_por_nombre[cat_data["nombre"]] = existente

        # 3. Productos (al menos 8 con stock e imagen_url, idempotentes)
        productos_data = [
            {
                "categoria_id": categorias_por_nombre["Pizzas"].id,
                "nombre": "Pizza Muzzarella",
                "descripcion": "Salsa de tomate, muzzarella y orégano",
                "precio_base": 8500.0,
                "imagen_url": "/images/productos/pizza-muzzarella.jpg",
                "stock": 20,
                "disponible": True,
                "activo": True,
            },
            {
                "categoria_id": categorias_por_nombre["Pizzas"].id,
                "nombre": "Pizza Napolitana",
                "descripcion": "Muzzarella, rodajas de tomate, ajo y aceitunas",
                "precio_base": 9200.0,
                "imagen_url": "/images/productos/pizza-napolitana.jpg",
                "stock": 15,
                "disponible": True,
                "activo": True,
            },
            {
                "categoria_id": categorias_por_nombre["Pizzas"].id,
                "nombre": "Pizza Fugazzeta",
                "descripcion": "Abundante cebolla y muzzarella",
                "precio_base": 9000.0,
                "imagen_url": "/images/productos/pizza-fugazzeta.jpg",
                "stock": 12,
                "disponible": True,
                "activo": True,
            },
            {
                "categoria_id": categorias_por_nombre["Hamburguesas"].id,
                "nombre": "Burger Clásica",
                "descripcion": "Medallón de carne, cheddar, lechuga y tomate",
                "precio_base": 7800.0,
                "imagen_url": "/images/productos/burger-clasica.jpg",
                "stock": 25,
                "disponible": True,
                "activo": True,
            },
            {
                "categoria_id": categorias_por_nombre["Hamburguesas"].id,
                "nombre": "Burger Doble Bacon",
                "descripcion": "Doble carne, doble cheddar y panceta crocante",
                "precio_base": 9800.0,
                "imagen_url": "/images/productos/burger-doble-bacon.jpg",
                "stock": 18,
                "disponible": True,
                "activo": True,
            },
            {
                "categoria_id": categorias_por_nombre["Bebidas"].id,
                "nombre": "Gaseosa Cola 1.5L",
                "descripcion": "Botella retornable o descartable bien fría",
                "precio_base": 2800.0,
                "imagen_url": "/images/productos/gaseosa-cola.jpg",
                "stock": 30,
                "disponible": True,
                "activo": True,
            },
            {
                "categoria_id": categorias_por_nombre["Bebidas"].id,
                "nombre": "Agua sin Gas 500ml",
                "descripcion": "Agua mineral natural",
                "precio_base": 1500.0,
                "imagen_url": "/images/productos/agua-sin-gas.jpg",
                "stock": 40,
                "disponible": True,
                "activo": True,
            },
            {
                "categoria_id": categorias_por_nombre["Postres"].id,
                "nombre": "Flan Casero con Dulce",
                "descripcion": "Flan de vainilla con dulce de leche y crema",
                "precio_base": 3500.0,
                "imagen_url": "/images/productos/flan-casero.jpg",
                "stock": 14,
                "disponible": True,
                "activo": True,
            },
        ]

        for prod_data in productos_data:
            existente_prod = session.exec(
                select(Producto).where(Producto.nombre == prod_data["nombre"])
            ).first()
            if not existente_prod:
                nuevo_prod = Producto(**prod_data)
                session.add(nuevo_prod)
                session.commit()
                print(f"  - Producto creado: {prod_data['nombre']} (stock: {prod_data['stock']})")
            else:
                if existente_prod.imagen_url != prod_data["imagen_url"]:
                    existente_prod.imagen_url = prod_data["imagen_url"]
                    session.add(existente_prod)
                    session.commit()
                print(f"  - Producto ya existente: {prod_data['nombre']}")

        print("Seed completado correctamente.")


if __name__ == "__main__":
    seed_data()