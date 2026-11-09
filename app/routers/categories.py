from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categorias"])


@router.get("/", response_model=List[CategoryResponse], summary="Listar categorias")
def list_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """
    Lista todas las categorias del catalogo bibliotecario.
    """
    return db.query(Category).offset(skip).limit(limit).all()


@router.get("/{category_id}", response_model=CategoryResponse, summary="Obtener categoria por ID")
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """
    Obtiene la informacion de una categoria por su identificador unico.
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria no encontrada")
    return category


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, summary="Crear nueva categoria")
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRADOR", "BIBLIOTECARIO"]))
):
    """
    Registra una categoria de libros. Solo administradores y bibliotecarios tienen permiso.
    """
    existing = db.query(Category).filter(Category.nombre == category_in.nombre).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una categoria con ese nombre"
        )

    category = Category(**category_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryResponse, summary="Actualizar categoria")
def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRADOR", "BIBLIOTECARIO"]))
):
    """
    Modifica una categoria existente.
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria no encontrada")

    for field, value in category_update.model_dump(exclude_unset=True).items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar categoria")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRADOR", "BIBLIOTECARIO"]))
):
    """
    Elimina una categoria si no tiene libros asociados para asegurar la integridad referencial.
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria no encontrada")

    if category.books:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar la categoria porque tiene libros asociados en el catalogo"
        )

    db.delete(category)
    db.commit()
    return None
