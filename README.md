# API REST para el Manejo de un Sistema Bibliotecario

**Asignatura:** Utilización de Frameworks para el Desarrollo de Software  
**Docente:** Oscar Alfredo Cruz Rovira  
**Ciclo:** II 2026  

---

## 1. Descripción del Proyecto

Esta solución consiste en una **API REST robusta, escalable y segura** desarrollada con **FastAPI** y **PostgreSQL** (con soporte SQLAlchemy ORM) para administrar de forma centralizada las operaciones de una biblioteca universitaria o pública.

El sistema resuelve la problemática de gestión de recursos bibliográficos implementando:
* Control de acceso basado en roles (**RBAC**): `ADMINISTRADOR`, `BIBLIOTECARIO` y `USUARIO`.
* Autenticación segura mediante **JWT (JSON Web Tokens)** con tiempo de expiración y hash de contraseñas con **Bcrypt**.
* Catálogo bibliográfico completo: gestión de **Libros**, **Autores** y **Categorías**.
* Gestión de **Préstamos** y **Devoluciones** con control atómico de disponibilidad en tiempo real.
* Validación exhaustiva de datos de entrada mediante esquemas **Pydantic v2**.
* Protección de integridad referencial (prevención de borrados en cascada no deseados).
* Documentación interactiva autogenerada bajo estándar OpenAPI (**Swagger UI** y **ReDoc**).
* Suite automatizada de pruebas con **Pytest** que cubre al 100% los **10 casos de prueba obligatorios**.

---

## 2. Arquitectura y Estructura del Código

El proyecto sigue una arquitectura limpia en capas modularizada por responsabilidades:

```text
Api_FinalR/
├── app/
│   ├── core/               # Configuracion global, conexion a DB y utilidades de seguridad
│   │   ├── config.py       # Lectura de variables de entorno (Pydantic Settings)
│   │   ├── database.py     # Sesion SQLAlchemy y Dependency Injection
│   │   └── security.py     # Hashing con Bcrypt y firma/verificacion de tokens JWT
│   ├── models/             # Modelos de base de datos relacional (ORM)
│   │   ├── role.py         # Entidad Roles (ADMINISTRADOR, BIBLIOTECARIO, USUARIO)
│   │   ├── user.py         # Entidad Usuarios y credenciales protegidas
│   │   ├── author.py       # Entidad Autores bibliograficos
│   │   ├── category.py     # Entidad Categorias literarias
│   │   ├── book.py         # Entidad Libros y control de ejemplares disponibles
│   │   └── loan.py         # Entidad Prestamos y Devoluciones
│   ├── schemas/            # Esquemas de validacion y serializacion DTO (Pydantic)
│   │   ├── auth.py         # Solicitudes de login y respuestas de tokens
│   │   ├── user.py         # Validacion de datos de usuario y filtros de salida
│   │   ├── role.py         # Esquemas para roles
│   │   ├── author.py       # Validacion de autores
│   │   ├── category.py     # Validacion de categorias
│   │   ├── book.py         # Validacion de libros, ISBN y cantidades
│   │   └── loan.py         # Validacion de solicitud y retorno de prestamos
│   ├── routers/            # Controladores y endpoints REST
│   │   ├── auth.py         # /api/v1/auth (Login, registro, perfil actual)
│   │   ├── users.py        # /api/v1/users (Gestion y asignacion de roles)
│   │   ├── authors.py      # /api/v1/authors (CRUD de autores)
│   │   ├── categories.py   # /api/v1/categories (CRUD de categorias)
│   │   ├── books.py        # /api/v1/books (CRUD de libros y filtros avanzados)
│   │   └── loans.py        # /api/v1/loans (Prestamos y devoluciones)
│   ├── dependencies.py     # Inyeccion de dependencias: autenticacion y RBAC
│   ├── main.py             # Punto de entrada de la aplicacion FastAPI y CORS
│   └── seeds.py            # Semilla de datos para pruebas y demostracion
├── tests/                  # Suite de pruebas automatizadas
│   ├── conftest.py         # Fixtures de base de datos aislada y TestClient
│   └── test_api_mandatory.py # Implementacion de los 10 casos de prueba obligatorios
├── .env.example            # Plantilla de variables de entorno
├── requirements.txt        # Dependencias fijadas del proyecto
└── README.md               # Documentacion tecnica del sistema
```

---

## 3. Requisitos Previos

* **Python 3.10+** (probado y compatible con Python 3.11, 3.12, 3.13 y 3.14)
* **PostgreSQL** (versión 13 o superior) o **SQLite** para entornos de desarrollo local rápido.
* **Git**

---

## 4. Instalación y Puesta en Marcha

### Paso 1: Clonar o posicionarse en el repositorio
```bash
git clone https://github.com/SrMochi02/API-proyecto-final.git
cd API-proyecto-final
```

### Paso 2: Crear y activar el entorno virtual
En Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
En Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Configurar variables de entorno
Copia el archivo `.env.example` como `.env`:
```powershell
copy .env.example .env
```

Configura tu cadena de conexión a PostgreSQL en `.env`:
```ini
DATABASE_URL=postgresql://usuario:password@localhost:5432/biblioteca_db
```
*(Nota: Para pruebas locales inmediatas o desarrollo offline, también puedes utilizar `DATABASE_URL=sqlite:///./biblioteca.db`).*

### Paso 5: Poblar datos iniciales para la demostración
Ejecuta el script seeder que crea los roles, usuarios de demostración, autores, categorías y libros:
```bash
python -m app.seeds
```

### Paso 6: Iniciar el servidor de desarrollo
```bash
uvicorn app.main:app --reload
```

El servidor quedará disponible en:
* **API Principal:** `http://127.0.0.1:8000`
* **Documentación Interactiva (Swagger UI):** `http://127.0.0.1:8000/docs`
* **Documentación Alternativa (ReDoc):** `http://127.0.0.1:8000/redoc`

---

## 5. Cuentas de Prueba Preconfiguradas

Para la demostración técnica ante el docente sin modificar la base de datos manualmente, se cuenta con los siguientes usuarios generados por `app/seeds.py`:

| Rol | Username | Contraseña | Permisos |
| :--- | :--- | :--- | :--- |
| **ADMINISTRADOR** | `admin` | `adminpassword123` | Control total del sistema, gestión de usuarios, roles, catálogo y préstamos. |
| **BIBLIOTECARIO** | `bibliotecario` | `bibliopassword123` | Gestión de autores, categorías, libros, registro y devolución de préstamos. |
| **USUARIO** | `estudiante` | `studentpassword123` | Consulta del catálogo, solicitud de préstamos personales y consulta de historial propio. |

---

## 6. Endpoints Principales de la API

Todos los endpoints se encuentran prefijados por `/api/v1`:

### Autenticación (`/api/v1/auth`)
* `POST /auth/login`: Autentica credenciales y genera el token Bearer JWT.
* `POST /auth/register`: Registro de nuevos usuarios.
* `GET /auth/me`: Retorna los datos del usuario autenticado (requiere token).

### Usuarios y Roles (`/api/v1/users`)
* `GET /users/`: Listar todos los usuarios *(Admin y Bibliotecario)*.
* `GET /users/roles`: Listar roles disponibles.
* `GET /users/{id}`: Detalle de usuario *(Admin, Bibliotecario o cuenta propia)*.
* `POST /users/`: Crear usuario asignando rol *(Solo Admin)*.
* `PUT /users/{id}`: Actualizar usuario *(Admin o cuenta propia)*.
* `DELETE /users/{id}`: Eliminación/desactivación con protección de historial *(Solo Admin)*.

### Catálogo de Autores y Categorías
* `GET /authors/` | `POST /authors/` | `PUT /authors/{id}` | `DELETE /authors/{id}`
* `GET /categories/` | `POST /categories/` | `PUT /categories/{id}` | `DELETE /categories/{id}`
*(Creación, edición y eliminación restringidas a Admin y Bibliotecario; se impide la eliminación si existen libros asociados).*

### Catálogo de Libros (`/api/v1/books`)
* `GET /books/`: Consulta con filtros (`autor_id`, `categoria_id`, `disponible`, `search`, `skip`, `limit`).
* `GET /books/{id}`: Detalle completo de libro con autor y categoría.
* `POST /books/`: Registro de libro con validación de ISBN único y existencia de autor/categoría.
* `PUT /books/{id}`: Actualización de datos y ajuste automático de disponibilidad.
* `DELETE /books/{id}`: Eliminación protegida (se rechaza si tiene préstamos activos).

### Préstamos y Devoluciones (`/api/v1/loans`)
* `POST /loans/`: Solicitud de préstamo (valida disponibilidad de ejemplares en tiempo real).
* `POST /loans/{id}/return`: Registro de devolución y restauración inmediata de disponibilidad del ejemplar.
* `GET /loans/`: Listado general con filtros por estado (`ACTIVO`, `DEVUELTO`, `VENCIDO`) *(Admin y Bibliotecario)*.
* `GET /loans/my-loans`: Consulta del historial y préstamos activos del usuario en sesión.
* `GET /loans/{id}`: Detalle de préstamo.

---

## 7. Reglas de Negocio Implementadas

1. **Disponibilidad Estricta:** No es posible prestar un ejemplar si `ejemplares_disponibles <= 0` o `disponible == False` (HTTP 400).
2. **Restauración en Devolución:** Al registrar la devolución de un préstamo activo, se marca la fecha real de retorno y el ejemplar vuelve a incrementar la disponibilidad en el catálogo.
3. **Seguridad y Privacidad en Login:** Ante credenciales inválidas, el sistema retorna un mensaje genérico unificado (`HTTP 401: Credenciales de acceso invalidas`) sin exponer si el usuario existe o no.
4. **Control de Acceso (RBAC):** Las operaciones de mutación del catálogo bibliográfico y administración de usuarios están estrictamente restringidas a roles con privilegios (`HTTP 403 Forbidden`).
5. **Integridad Referencial:** Se impide eliminar autores o categorías que tengan libros enlazados, así como libros que cuenten con préstamos activos.

---

## 8. Casos de Prueba Obligatorios y Ejecución

La suite de pruebas automatizadas con **Pytest** verifica los 10 casos obligatorios del requerimiento:

| # | Prueba Obligatoria | Endpoint Involucrado | Evidencia / Comportamiento Verificado |
| :-: | :--- | :--- | :--- |
| **1** | **Login válido** | `POST /auth/login` | Emisión exitosa de token JWT, tipo Bearer y datos del usuario autenticado. |
| **2** | **Login inválido** | `POST /auth/login` | Rechazo con código 401 sin revelar existencia de usuario ni información sensible. |
| **3** | **Ruta protegida sin token** | `GET /auth/me` | Rechazo con código 401 indicando ausencia de token. |
| **4** | **Token inválido o expirado** | `GET /auth/me` | Rechazo con código 401 por firma inválida o timestamp de expiración superado. |
| **5** | **Acción sin permiso** | `POST /books/` | Un usuario con rol regular recibe código 403 Forbidden al intentar crear libros. |
| **6** | **CRUD de libro** | `/books/` (CRUD) | Creación, lectura, actualización y eliminación controlada del libro. |
| **7** | **Préstamo válido** | `POST /loans/` | Registro del préstamo y decremento de ejemplares disponibles a 0 (`disponible=False`). |
| **8** | **Préstamo inválido** | `POST /loans/` | Rechazo con código 400 al intentar prestar un libro sin ejemplares disponibles. |
| **9** | **Devolución** | `POST /loans/{id}/return` | Registro de retorno y reactivación de disponibilidad del libro (`disponible=True`). |
| **10** | **Datos inválidos** | `POST /auth/register` | Rechazo con código 422 Unprocessable Entity por validación Pydantic. |

### Para ejecutar los tests:
```bash
python -m pytest -v
```

Resultado esperado:
```text
tests/test_api_mandatory.py::test_case_01_login_valido PASSED            [ 10%]
tests/test_api_mandatory.py::test_case_02_login_invalido PASSED          [ 20%]
tests/test_api_mandatory.py::test_case_03_ruta_protegida_sin_token PASSED [ 30%]
tests/test_api_mandatory.py::test_case_04_token_invalido_o_expirado PASSED [ 40%]
tests/test_api_mandatory.py::test_case_05_accion_sin_permiso PASSED      [ 50%]
tests/test_api_mandatory.py::test_case_06_crud_libro PASSED              [ 60%]
tests/test_api_mandatory.py::test_case_07_prestamo_valido PASSED         [ 70%]
tests/test_api_mandatory.py::test_case_08_prestamo_invalido PASSED       [ 80%]
tests/test_api_mandatory.py::test_case_09_devolucion PASSED              [ 90%]
tests/test_api_mandatory.py::test_case_10_datos_invalidos PASSED         [100%]

======================== 10 passed in 2.20s ========================
```
