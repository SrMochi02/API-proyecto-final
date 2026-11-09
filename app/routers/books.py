from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.book import Book
from app.models.author import Author
from app.models.category import Category
from app.models.loan import Loan
from app.models.user import User
from app.schemas.book import BookCreate, BookUpdate, BookResponse

router = APIRouter(prefix="/books", tags=["Libros"])


@router.get("/", response_model=List[BookResponse], summary="Consultar catalogo de libros")
def list_books(
    skip: int = 0,
    limit: int = 100,
    autor_id: Optional[int] = Query(None, description="Filtrar por autor"),
    categoria_id: Optional[int] = Query(None, description="Filtrar por categoria"),
    disponible: Optional[bool] = Query(None, description="Filtrar por disponibilidad"),
    search: Optional[str] = Query(None, description="Buscar por titulo o ISBN"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """
    Consulta el catalogo bibliografico con soporte de filtros por autor, categoria,
    disponibilidad y busqueda por texto.
    """
    query = db.query(Book)

    if autor_id is not None:
        query = query.filter(Book.autor_id == autor_id)
    if categoria_id is not None:
        query = query.filter(Book.categoria_id == categoria_id)
    if disponible is not None:
        query = query.filter(Book.disponible == disponible)
    if search:
        search_filter = f"%{search}%"
        query = query.filter((Book.titulo.ilike(search_filter)) | (Book.isbn.ilike(search_filter)))

    return query.offset(skip).limit(limit).all()


@router.get("/{book_id}", response_model=BookResponse, summary="Obtener libro por ID")
def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """
    Retorna el detalle completo de un libro incluyendo su autor y categoria.
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Libro no encontrado")
    return book


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED, summary="Registrar nuevo libro")
def create_book(
    book_in: BookCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRADOR", "BIBLIOTECARIO"]))
):
    """
    Registra un nuevo libro en el catalogo. Verifica unicidad de ISBN y existencia de autor y categoria.
    """
    # Validar unicidad del ISBN
    existing_isbn = db.query(Book).filter(Book.isbn == book_in.isbn).first()
    if existing_isbn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un libro registrado con el ISBN {book_in.isbn}"
        )

    # Validar autor
    author = db.query(Author).filter(Author.id == book_in.autor_id).first()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El autor con ID {book_in.autor_id} no existe"
        )

    # Validar categoria
    category = db.query(Category).filter(Category.id == book_in.categoria_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La categoria con ID {book_in.categoria_id} no existe"
        )

    new_book = Book(
        titulo=book_in.titulo,
        isbn=book_in.isbn,
        anio_publicacion=book_in.anio_publicacion,
        autor_id=book_in.autor_id,
        categoria_id=book_in.categoria_id,
        ejemplares_totales=book_in.ejemplares_totales,
        ejemplares_disponibles=book_in.ejemplares_totales,
        disponible=book_in.ejemplares_totales > 0
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


@router.put("/{book_id}", response_model=BookResponse, summary="Actualizar libro")
def update_book(
    book_id: int,
    book_update: BookUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRADOR", "BIBLIOTECARIO"]))
):
    """
    Actualiza la informacion de un libro en el catalogo.
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Libro no encontrado")

    update_dict = book_update.model_dump(exclude_unset=True)

    if "isbn" in update_dict and update_dict["isbn"] != book.isbn:
        existing_isbn = db.query(Book).filter(Book.isbn == update_dict["isbn"]).first()
        if existing_isbn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El ISBN {update_dict['isbn']} ya pertenece a otro libro"
            )

    if "autor_id" in update_dict:
        author = db.query(Author).filter(Author.id == update_dict["autor_id"]).first()
        if not author:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Autor no existe")

    if "categoria_id" in update_dict:
        category = db.query(Category).filter(Category.id == update_dict["categoria_id"]).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria no existe")

    # Ajustar disponibilidad si se cambian los ejemplares totales
    if "ejemplares_totales" in update_dict:
        diferencia = update_dict["ejemplares_totales"] - book.ejemplares_totales
        nuevo_disponibles = book.ejemplares_disponibles + diferencia
        if nuevo_disponibles < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden reducir los ejemplares por debajo de la cantidad actualmente prestada"
            )
        book.ejemplares_disponibles = nuevo_disponibles
        book.disponible = book.ejemplares_disponibles > 0

    for field, value in update_dict.items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar libro")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRADOR", "BIBLIOTECARIO"]))
):
    """
    Elimina un libro del sistema. Previene eliminacion si existen prestamos activos.
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Libro no encontrado")

    # Verificar si tiene prestamos activos
    prestamo_activo = db.query(Loan).filter(
        Loan.libro_id == book_id,
        Loan.estado == "ACTIVO"
    ).first()
    if prestamo_activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el libro porque tiene ejemplares con prestamos activos"
        )

    db.delete(book)
    db.commit()
    return None
