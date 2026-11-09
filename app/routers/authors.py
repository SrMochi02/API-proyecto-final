from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.author import Author
from app.models.user import User
from app.schemas.author import AuthorCreate, AuthorUpdate, AuthorResponse

router = APIRouter(prefix="/authors", tags=["Autores"])


@router.get("/", response_model=List[AuthorResponse], summary="Listar autores")
def list_authors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """
    Lista todos los autores registrados en el catalogo bibliotecario.
    """
    return db.query(Author).offset(skip).limit(limit).all()


@router.get("/{author_id}", response_model=AuthorResponse, summary="Obtener autor por ID")
def get_author(
    author_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """
    Obtiene los detalles de un autor especifico.
    """
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Autor no encontrado")
    return author


@router.post("/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED, summary="Crear nuevo autor")
def create_author(
    author_in: AuthorCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRADOR", "BIBLIOTECARIO"]))
):
    """
    Registra un nuevo autor. Solo administradores y bibliotecarios tienen permiso.
    """
    author = Author(**author_in.model_dump())
    db.add(author)
    db.commit()
    db.refresh(author)
    return author


@router.put("/{author_id}", response_model=AuthorResponse, summary="Actualizar autor")
def update_author(
    author_id: int,
    author_update: AuthorUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRADOR", "BIBLIOTECARIO"]))
):
    """
    Modifica la informacion de un autor.
    """
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Autor no encontrado")

    for field, value in author_update.model_dump(exclude_unset=True).items():
        setattr(author, field, value)

    db.commit()
    db.refresh(author)
    return author


@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar autor")
def delete_author(
    author_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRADOR", "BIBLIOTECARIO"]))
):
    """
    Elimina un autor si no tiene libros asociados para preservar la integridad referencial.
    """
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Autor no encontrado")

    if author.books:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el autor porque tiene libros asociados en el catalogo"
        )

    db.delete(author)
    db.commit()
    return None
