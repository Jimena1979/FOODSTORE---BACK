# Trabajo Práctico Integrador - Full Stack (FastAPI + React)
**Tecnicatura Universitaria en Programación a Distancia - UTN**  
**Materia: Programación IV — Unidad 9: Seguridad, Estado Global con Zustand y Autenticación**

---

## 📋 1. Descripción General del Proyecto

Este repositorio incluye la implementación full stack del sistema **Food Store**, correspondiente al Trabajo Práctico de la Unidad 9. El sistema incorpora un módulo completo de **Identidad & Acceso**, autenticación mediante **JWT transportado en cookies HttpOnly**, autorización basada en roles (**RBAC** con `UsuarioRol`), baja lógica (`deleted_at`), cliente HTTP con **Axios e interceptores**, gestión de estado global mediante **Zustand con middleware persist**, y **rutas protegidas en React**.

## ⚙️ 2. Configuración de Variables de Entorno

### Backend (`.env`)
Crear un archivo `.env` en la raíz del backend utilizando de base el `.env.example`:
```env
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/foodstore_db
SECRET_KEY=clave_secreta_jwt_super_segura
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend (`.env`)
Crear un archivo `.env` en la raíz del frontend:
```env
VITE_API_URL=http://localhost:8000
```

---

## 🚀 4. Guía de Instalación y Ejecución

### A. Configuración del Backend (FastAPI)

1. **Abrir la terminal en la carpeta del backend y crear el entorno virtual**:
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En macOS/Linux:
   source .venv/bin/activate
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar el Script Seed (Generación de Roles y Usuarios Iniciales)**:
   Antes de iniciar la API por primera vez, se debe ejecutar el script `seed.py`. Este script se encarga de poblar las tablas de catálogo, crear los roles obligatorios (`admin` y `user`) y registrar al usuario administrador inicial:
   ```bash
   python seed.py
   ```

4. **Iniciar el servidor backend**:
   ```bash
   uvicorn app.main:app --reload
   ```
   *(Backend disponible en `http://localhost:8000` y documentación Swagger UI en `http://localhost:8000/docs`)*.

---

### B. Configuración del Frontend (React + Vite)

1. **Abrir la terminal en la carpeta del frontend**:
   ```bash
   npm install
   ```

2. **Iniciar la aplicación frontend**:
   ```bash
   npm run dev
   ```
   *(La aplicación correrá en `http://localhost:5173`)*.

---

## 🔐 5. Reglas de Negocio y Seguridad Aplicadas

1. **Autenticación JWT en Cookie HttpOnly**:
   - El token de acceso se genera en el endpoint `POST /api/v1/auth/token` y se envía automáticamente al navegador mediante la cabecera `Set-Cookie` como una cookie **HttpOnly**. Esto evita que scripts maliciosos accedan al JWT mediante `document.cookie` (protección contra XSS).

2. **Control de Acceso Basado en Roles (RBAC)**:
   - Las operaciones de creación, edición y eliminación de categorías y productos están restringidas a usuarios con rol `admin` mediante la dependencia `require_role(["admin"])`.
   - La validez del rol verifica la tabla `UsuarioRol`, excluyendo roles con fecha `expires_at` vencida.

3. **Baja Lógica (`deleted_at`)**:
   - El borrado de entidades principales (usuarios, categorías, productos) se realiza mediante marcado de fecha en `deleted_at`/ `activo`. Los listados generales omiten los registros marcados como eliminados.
   - En la administración de usuarios, la baja lógica se opera mediante `/admin/usuarios/{id}/desactivar` y `/activar`. Un usuario desactivado no puede autenticarse ni consumir endpoints protegidos (devuelve error 400).

4. **Cliente Axios con Interceptores**:
   - Configurado con `withCredentials: true` para adjuntar la cookie en cada petición.
   - Interceptor de respuesta configurado para capturar errores `401 Unauthorized` de forma centralizada y limpiar el estado de autenticación en Zustand.

5. **Estado Global con Zustand y Persistencia**:
   - El `useAuthStore` conserva los datos públicos del usuario autenticado y sus roles vigentes. Utiliza el middleware `persist` parcializado para resguardar la sesión en recargas de página sin almacenar nunca tokens sensibles en JavaScript.

6. **Interfaz Condicional y Rutas Protegidas**:
   - `ProtectedRoute` restringe el paso a las vistas privadas según el estado de sesión y los roles requeridos, redirigiendo a `/login` o `/unauthorized`.
   - La barra de navegación (`Navbar`) y los paneles ocultan los botones de acción administrativa a usuarios con rol regular (`user`).