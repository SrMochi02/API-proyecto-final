from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.role import RoleResponse

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/", response_model=List[UserResponse], summary="Listar usuarios (Admin y Bibliotecario)")
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRADOR", "BIBLIOTECARIO"]))
):
    """
    Ruta protegida para administradores y bibliotecarios para consultar la lista de usuarios.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/roles", response_model=List[RoleResponse], summary="Listar roles del sistema")
def list_roles(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """
    Lista todos los roles disponibles en el sistema.
    """
    return db.query(Role).all()


@router.get("/{user_id}", response_model=UserResponse, summary="Obtener usuario por ID")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene los datos de un usuario. Los usuarios normales solo pueden consultarse a si mismos;
    administradores y bibliotecarios pueden consultar a cualquiera.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    role_name = current_user.role.name if current_user.role else ""
    if role_name not in ["ADMINISTRADOR", "BIBLIOTECARIO"] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para ver la informacion de otro usuario"
        )

    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Crear usuario con rol especifico (Solo Admin)")
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRADOR"]))
):
    """
    Permite al administrador crear usuarios asignando directamente cualquier rol.
    """
    existing = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de usuario o correo electronico ya registrado"
        )

    role = db.query(Role).filter(Role.id == user_in.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol con ID {user_in.role_id} no existe"
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


@router.put("/{user_id}", response_model=UserResponse, summary="Actualizar usuario")
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza la informacion de un usuario.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    role_name = current_user.role.name if current_user.role else ""
    is_admin = role_name == "ADMINISTRADOR"

    if not is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para modificar otro usuario"
        )

    # Solo el admin puede cambiar roles o estado activo
    if not is_admin:
        if user_update.role_id is not None or user_update.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden cambiar roles o el estado activo de una cuenta"
            )

    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    elif "password" in update_data:
        update_data.pop("password")

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desactivar o eliminar usuario (Solo Admin)")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRADOR"]))
):
    """
    Elimina o desactiva un usuario. Si tiene prestamos registrados, se desactiva para mantener integridad referencial.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    if user.loans:
        # Politica de integridad referencial: soft delete si tiene historial
        user.is_active = False
        db.commit()
        return None

    db.delete(user)
    db.commit()
    return None
