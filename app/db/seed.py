"""
Script de inicialización para poblar la base de datos con datos de catálogo y usuario admin.

Ejecución:
    python -m app.db.seed
"""

from sqlmodel import Session, select

from app.core.database import (
    create_db_and_tables,
    engine,
)
from app.core.security import hash_password
from app.usuario.models import Rol, Usuario, UsuarioRol


def seed_data():
    # 1. Asegurar la creación de tablas
    create_db_and_tables()

    with Session(engine) as session:
        print("🌱 Iniciando carga de datos iniciales (seed)...")

        # ─── 1. Carga de Roles de Catálogo (RN-06) ──────────────────────────────
        roles_base = [
            {"nombre": "admin", "descripcion": "Administrador del sistema con acceso completo"},
            {"nombre": "user", "descripcion": "Usuario cliente/estándar del sistema"},
        ]

        roles_db = {}
        for r_data in roles_base:
            statement = select(Rol).where(Rol.nombre == r_data["nombre"])
            rol_existente = session.exec(statement).first()

            if not rol_existente:
                rol_existente = Rol(nombre=r_data["nombre"], descripcion=r_data["descripcion"])
                session.add(rol_existente)
                session.commit()
                session.refresh(rol_existente)
                print(f"  └─ Rol creado: '{rol_existente.nombre}'")
            else:
                print(f"  └─ Rol ya existente: '{rol_existente.nombre}'")
            
            roles_db[r_data["nombre"]] = rol_existente

        # 2. Carga de Usuario Admin Inicial
        admin_email = "admin@foodstore.com"
        statement_admin = select(Usuario).where(Usuario.email == admin_email)
        admin_user = session.exec(statement_admin).first()

        if not admin_user:
            admin_user = Usuario(
                nombre="Admin",
                apellido="Sistema",
                email=admin_email,
                celular="111222333",
                password_hash=hash_password("admin1234"),
            )
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)

            # Asignar rol 'admin' en UsuarioRol
            usuario_rol = UsuarioRol(
                usuario_id=admin_user.id,
                rol_id=roles_db["admin"].id,
                asignado_por_id=None,
            )
            session.add(usuario_rol)
            session.commit()
            print(f"  └─ Usuario administrador creado: {admin_email} (Password: admin1234)")
        else:
            print(f"  └─ Usuario administrador ya existente: {admin_email}")

        # 3. Carga de Usuario Estándar (Cliente) de Prueba
        user_email = "user@foodstore.com"
        statement_user = select(Usuario).where(Usuario.email == user_email)
        standard_user = session.exec(statement_user).first()

        if not standard_user:
            standard_user = Usuario(
                nombre="Cliente",
                apellido="Regular",
                email=user_email,
                celular="444555666",
                password_hash=hash_password("user1234"),
            )
            session.add(standard_user)
            session.commit()
            session.refresh(standard_user)

            # Asignar rol 'user' en UsuarioRol
            usuario_rol_std = UsuarioRol(
                usuario_id=standard_user.id,
                rol_id=roles_db["user"].id,
                asignado_por_id=None,
            )
            session.add(usuario_rol_std)
            session.commit()
            print(f"  └─ Usuario estándar creado: {user_email} (Password: user1234)")
        else:
            print(f"  └─ Usuario estándar ya existente: {user_email}")

        print("✅ Proceso de seed completado exitosamente.")


if __name__ == "__main__":
    seed_data()