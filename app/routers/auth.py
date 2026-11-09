from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.dependencies import get_current_user
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Autenticacion"])


@router.post("/login", response_model=Token, summary="Inicio de sesion de usuario")
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Endpoint de login con validacion de credenciales seguras.
    
    Regla de negocio: Credenciales incorrectas nunca revelan si el usuario existe
    o si falló la contraseña para evitar ataques de enumeracion.
    """
    # Se busca por username o por email
    user = db.query(User).filter(
        (User.username == login_data.username) | (User.email == login_data.username)
    ).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso invalidas",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta de usuario inactiva. Contacte al administrador"
        )

    # Generar token JWT con claims minimos
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.name if user.role else "USUARIO"},
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Registro publico de usuario")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Permite registrar un nuevo usuario con credenciales hasheadas con bcrypt.
    """
    # Verificar si el username o email ya existen
    existing_user = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario o correo electronico ya se encuentra registrado"
        )

    # Verificar que el rol exista
    role = db.query(Role).filter(Role.id == user_in.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El rol con id {user_in.role_id} no existe"
        )

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role_id=user_in.role_id,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/me", response_model=UserResponse, summary="Obtener perfil del usuario autenticado actual")
def get_me(current_user: User = Depends(get_current_user)):
    """
    Ruta protegida que devuelve los datos del usuario a partir del token JWT Bearer.
    """
    return current_user
