from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient


def get_token(client: TestClient, username: str, password: str) -> str:
    """Helper para obtener el token JWT de un usuario."""
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    return res.json()["access_token"]


# ==============================================================================
# CASO 1: Login válido
# ==============================================================================
def test_case_01_login_valido(client: TestClient):
    """
    Caso 1: Login valido.
    Evidencia esperada: Se obtiene token y datos minimos necesarios para autenticacion.
    """
    response = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert "user" in data
    assert data["user"]["username"] == "admin_test"
    assert data["user"]["email"] == "admin@test.com"
    assert data["user"]["role"]["name"] == "ADMINISTRADOR"


# ==============================================================================
# CASO 2: Login inválido
# ==============================================================================
def test_case_02_login_invalido(client: TestClient):
    """
    Caso 2: Login invalido.
    Evidencia esperada: Se rechaza el acceso sin exponer si el usuario existe
    ni información sensible (401 Unauthorized con mensaje generico).
    """
    # Intento 1: Usuario inexistente
    res_no_user = client.post("/api/v1/auth/login", json={
        "username": "usuario_fantasma_inexistente",
        "password": "password123"
    })
    assert res_no_user.status_code == 401
    assert "Credenciales de acceso invalidas" in res_no_user.json()["detail"]

    # Intento 2: Usuario existente pero contraseña incorrecta
    res_wrong_pw = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "contraseña_completamente_erronea"
    })
    assert res_wrong_pw.status_code == 401
    # Ambos devuelven exactamente la misma respuesta para evitar ataques de enumeracion
    assert res_no_user.json()["detail"] == res_wrong_pw.json()["detail"]


# ==============================================================================
# CASO 3: Ruta protegida sin token
# ==============================================================================
def test_case_03_ruta_protegida_sin_token(client: TestClient):
    """
    Caso 3: Ruta protegida sin token.
    Evidencia esperada: La API deniega el acceso con respuesta HTTP apropiada (401).
    """
    # Intentar acceder al perfil protegido sin encabezado de autorizacion
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Token de acceso no proporcionado" in response.json()["detail"]


# ==============================================================================
# CASO 4: Token inválido o expirado
# ==============================================================================
def test_case_04_token_invalido_o_expirado(client: TestClient):
    """
    Caso 4: Token invalido o expirado.
    Evidencia esperada: La API rechaza la solicitud (401).
    """
    # 4a. Token corrupto/falso
    headers_invalid = {"Authorization": "Bearer token_falso_invalido_12345"}
    res_invalid = client.get("/api/v1/auth/me", headers=headers_invalid)
    assert res_invalid.status_code == 401
    assert "Token de acceso invalido" in res_invalid.json()["detail"]

    # 4b. Token expirado
    from app.core.security import create_access_token
    token_expirado = create_access_token(
        data={"sub": "admin_test"},
        expires_delta=timedelta(seconds=-60) # Ya expiro hace un minuto
    )
    headers_expired = {"Authorization": f"Bearer {token_expirado}"}
    res_expired = client.get("/api/v1/auth/me", headers=headers_expired)
    assert res_expired.status_code == 401
    assert "expirado" in res_expired.json()["detail"]


# ==============================================================================
# CASO 5: Acción sin permiso
# ==============================================================================
def test_case_05_accion_sin_permiso(client: TestClient):
    """
    Caso 5: Accion sin permiso.
    Evidencia esperada: Un usuario autenticado sin privilegios no puede ejecutar
    la operacion (403 Forbidden).
    """
    token_user = get_token(client, "user_test", "user123")
    headers = {"Authorization": f"Bearer {token_user}"}

    # Un usuario con rol 'USUARIO' intenta crear un libro (solo permitido a ADMIN o BIBLIOTECARIO)
    nuevo_libro = {
        "titulo": "Libro Prohibido",
        "isbn": "978-9999999999",
        "anio_publicacion": 2024,
        "autor_id": 1,
        "categoria_id": 1,
        "ejemplares_totales": 1
    }
    response = client.post("/api/v1/books/", json=nuevo_libro, headers=headers)
    assert response.status_code == 403
    assert "Accion no permitida" in response.json()["detail"]


# ==============================================================================
# CASO 6: CRUD de libro
# ==============================================================================
def test_case_06_crud_libro(client: TestClient):
    """
    Caso 6: CRUD de libro.
    Evidencia esperada: Crear, consultar, actualizar y eliminar/gestionar
    restricciones correctamente.
    """
    token_admin = get_token(client, "admin_test", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}

    # 1. CREATE
    libro_payload = {
        "titulo": "Rayuela",
        "isbn": "978-8437604572",
        "anio_publicacion": 1963,
        "autor_id": 1,
        "categoria_id": 1,
        "ejemplares_totales": 2
    }
    res_create = client.post("/api/v1/books/", json=libro_payload, headers=headers)
    assert res_create.status_code == 201
    book_id = res_create.json()["id"]
    assert res_create.json()["titulo"] == "Rayuela"
    assert res_create.json()["disponible"] is True

    # 2. READ (consultar por ID)
    res_get = client.get(f"/api/v1/books/{book_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["isbn"] == "978-8437604572"

    # 3. UPDATE
    res_update = client.put(f"/api/v1/books/{book_id}", json={
        "titulo": "Rayuela (Edicion Conmemorativa)"
    }, headers=headers)
    assert res_update.status_code == 200
    assert res_update.json()["titulo"] == "Rayuela (Edicion Conmemorativa)"

    # 4. DELETE
    res_delete = client.delete(f"/api/v1/books/{book_id}", headers=headers)
    assert res_delete.status_code == 204

    # Verificar que ya no existe
    res_after = client.get(f"/api/v1/books/{book_id}", headers=headers)
    assert res_after.status_code == 404


# ==============================================================================
# CASO 7: Préstamo válido
# ==============================================================================
def test_case_07_prestamo_valido(client: TestClient):
    """
    Caso 7: Prestamo valido.
    Evidencia esperada: El prestamo se registra y el ejemplar deja de estar disponible.
    """
    token_user = get_token(client, "user_test", "user123")
    headers = {"Authorization": f"Bearer {token_user}"}

    # El libro con id 1 tiene 1 solo ejemplar disponible inicialmente
    fecha_futura = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    prestamo_payload = {
        "libro_id": 1,
        "fecha_devolucion_esperada": fecha_futura,
        "observaciones": "Prestamo para lectura en clase"
    }
    response = client.post("/api/v1/loans/", json=prestamo_payload, headers=headers)
    assert response.status_code == 201
    loan_data = response.json()
    assert loan_data["estado"] == "ACTIVO"
    assert loan_data["libro_id"] == 1

    # Verificar que el ejemplar ya NO esta disponible
    res_book = client.get("/api/v1/books/1", headers=headers)
    assert res_book.status_code == 200
    assert res_book.json()["ejemplares_disponibles"] == 0
    assert res_book.json()["disponible"] is False


# ==============================================================================
# CASO 8: Préstamo inválido
# ==============================================================================
def test_case_08_prestamo_invalido(client: TestClient):
    """
    Caso 8: Prestamo invalido.
    Evidencia esperada: Se impide prestar un ejemplar no disponible (400 Bad Request).
    """
    token_biblio = get_token(client, "biblio_test", "biblio123")
    headers = {"Authorization": f"Bearer {token_biblio}"}

    # Intentar prestar el libro con id 1 (cuyos ejemplares estan en 0 debido al caso 7)
    fecha_futura = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    prestamo_payload = {
        "libro_id": 1,
        "fecha_devolucion_esperada": fecha_futura
    }
    response = client.post("/api/v1/loans/", json=prestamo_payload, headers=headers)
    assert response.status_code == 400
    assert "no tiene ejemplares disponibles" in response.json()["detail"]


# ==============================================================================
# CASO 9: Devolución
# ==============================================================================
def test_case_09_devolucion(client: TestClient):
    """
    Caso 9: Devolucion.
    Evidencia esperada: Se registra la devolucion y el ejemplar vuelve a estar disponible.
    """
    token_user = get_token(client, "user_test", "user123")
    headers = {"Authorization": f"Bearer {token_user}"}

    # Obtener el prestamo activo del usuario
    res_my_loans = client.get("/api/v1/loans/my-loans?estado=ACTIVO", headers=headers)
    assert res_my_loans.status_code == 200
    loans = res_my_loans.json()
    assert len(loans) > 0
    loan_id = loans[0]["id"]

    # Registrar devolucion
    res_return = client.post(f"/api/v1/loans/{loan_id}/return", json={
        "observaciones": "Devuelto en perfecto estado"
    }, headers=headers)
    assert res_return.status_code == 200
    assert res_return.json()["estado"] == "DEVUELTO"
    assert res_return.json()["fecha_devolucion_real"] is not None

    # Verificar que el libro con id 1 vuelve a estar disponible
    res_book = client.get("/api/v1/books/1", headers=headers)
    assert res_book.status_code == 200
    assert res_book.json()["ejemplares_disponibles"] == 1
    assert res_book.json()["disponible"] is True


# ==============================================================================
# CASO 10: Datos inválidos
# ==============================================================================
def test_case_10_datos_invalidos(client: TestClient):
    """
    Caso 10: Datos invalidos.
    Evidencia esperada: La API rechaza entradas que incumplen las reglas
    de validacion de esquemas Pydantic con codigo 422 Unprocessable Entity.
    """
    # 1. Registro con email invalido y password demasiado corto (<6 caracteres)
    payload_invalido = {
        "username": "us", # Menor al minimo de 3
        "email": "correo_sin_arroba_ni_dominio", # Invalido
        "password": "123", # Menor al minimo de 6
        "role_id": -5 # Negativo
    }
    response = client.post("/api/v1/auth/register", json=payload_invalido)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # Verifica que Pydantic capturo los campos invalidos
    fields_with_errors = [err["loc"][-1] for err in data["detail"]]
    assert "email" in fields_with_errors or "username" in fields_with_errors
