from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.book import Book
from app.models.loan import Loan
from app.models.user import User
from app.schemas.loan import LoanCreate, LoanReturn, LoanResponse

router = APIRouter(prefix="/loans", tags=["Prestamos y Devoluciones"])


@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED, summary="Registrar nuevo prestamo")
def create_loan(
    loan_in: LoanCreate,
    usuario_id: Optional[int] = Query(None, description="ID del usuario (solo admin/bibliotecario puede prestar a terceros)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Registra un prestamo cumpliendo las reglas de negocio:
    
    1. Regla: No se puede prestar un libro que no este disponible (ejemplares_disponibles <= 0).
    2. Regla: Registra usuario, libro, fecha_prestamo, fecha_devolucion_esperada y estado ACTIVO.
    3. Regla: Reduce los ejemplares disponibles y actualiza el estado de disponibilidad del libro.
    """
    role_name = current_user.role.name if current_user.role else ""
    target_user_id = current_user.id

    if usuario_id is not None:
        if role_name not in ["ADMINISTRADOR", "BIBLIOTECARIO"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores o bibliotecarios pueden solicitar prestamos para otro usuario"
            )
        target_user_id = usuario_id
        # Verificar que el usuario destino exista
        dest_user = db.query(User).filter(User.id == target_user_id).first()
        if not dest_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario destinatario no existe")

    # Bloquear el registro del libro para evitar condiciones de carrera (persistencia e integridad)
    book = db.query(Book).filter(Book.id == loan_in.libro_id).with_for_update().first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Libro no encontrado en el catalogo")

    # REGLA DE NEGOCIO OBLIGATORIA: Validacion de disponibilidad
    if not book.disponible or book.ejemplares_disponibles <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No es posible realizar el prestamo: el libro no tiene ejemplares disponibles actualmente"
        )

    # Validar que la fecha de devolucion esperada sea a futuro
    ahora = datetime.now(timezone.utc)
    fecha_esperada = loan_in.fecha_devolucion_esperada
    if fecha_esperada.tzinfo is None:
        fecha_esperada = fecha_esperada.replace(tzinfo=timezone.utc)

    if fecha_esperada <= ahora:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de devolucion esperada debe ser posterior a la fecha actual"
        )

    # Crear el prestamo
    new_loan = Loan(
        usuario_id=target_user_id,
        libro_id=book.id,
        fecha_devolucion_esperada=fecha_esperada,
        estado="ACTIVO",
        observaciones=loan_in.observaciones
    )
    db.add(new_loan)

    # Actualizar disponibilidad del ejemplar
    book.ejemplares_disponibles -= 1
    if book.ejemplares_disponibles == 0:
        book.disponible = False

    db.commit()
    db.refresh(new_loan)
    return new_loan


@router.post("/{loan_id}/return", response_model=LoanResponse, summary="Registrar devolucion de ejemplar")
def return_book(
    loan_id: int,
    return_in: Optional[LoanReturn] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Registra la devolucion de un libro prestado:
    
    1. Regla: Verifica que el prestamo exista y se encuentre en estado ACTIVO.
    2. Regla: Marca el estado como DEVUELTO y registra la fecha_devolucion_real.
    3. Regla: Incrementa los ejemplares disponibles del libro y vuelve a marcarlo como disponible.
    """
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de prestamo no encontrado")

    role_name = current_user.role.name if current_user.role else ""
    # Solo el propio usuario o el personal de la biblioteca puede registrar la devolucion
    if role_name not in ["ADMINISTRADOR", "BIBLIOTECARIO"] and loan.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene autorizacion para gestionar este prestamo"
        )

    if loan.estado != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El prestamo no se puede devolver porque ya se encuentra con estado '{loan.estado}'"
        )

    # Actualizar estado del prestamo
    loan.estado = "DEVUELTO"
    loan.fecha_devolucion_real = datetime.now(timezone.utc)
    if return_in and return_in.observaciones:
        loan.observaciones = (loan.observaciones or "") + " | Devolucion: " + return_in.observaciones

    # Actualizar disponibilidad del libro
    book = db.query(Book).filter(Book.id == loan.libro_id).with_for_update().first()
    if book:
        book.ejemplares_disponibles += 1
        book.disponible = True

    db.commit()
    db.refresh(loan)
    return loan


@router.get("/", response_model=List[LoanResponse], summary="Consultar todos los prestamos (Admin y Bibliotecario)")
def list_loans(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = Query(None, description="Filtrar por estado: ACTIVO, DEVUELTO, VENCIDO"),
    usuario_id: Optional[int] = Query(None, description="Filtrar por ID de usuario"),
    libro_id: Optional[int] = Query(None, description="Filtrar por ID de libro"),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRADOR", "BIBLIOTECARIO"]))
):
    """
    Consulta global de prestamos para gestion administrativa.
    """
    query = db.query(Loan)
    if estado:
        query = query.filter(Loan.estado == estado.upper())
    if usuario_id:
        query = query.filter(Loan.usuario_id == usuario_id)
    if libro_id:
        query = query.filter(Loan.libro_id == libro_id)

    return query.order_by(Loan.fecha_prestamo.desc()).offset(skip).limit(limit).all()


@router.get("/my-loans", response_model=List[LoanResponse], summary="Consultar mis prestamos activos e historico")
def get_my_loans(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permite al usuario autenticado consultar el listado de sus propios prestamos.
    """
    query = db.query(Loan).filter(Loan.usuario_id == current_user.id)
    if estado:
        query = query.filter(Loan.estado == estado.upper())
    return query.order_by(Loan.fecha_prestamo.desc()).all()


@router.get("/{loan_id}", response_model=LoanResponse, summary="Obtener detalle de prestamo por ID")
def get_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el detalle de un prestamo. Usuarios regulares solo pueden ver sus propios prestamos.
    """
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prestamo no encontrado")

    role_name = current_user.role.name if current_user.role else ""
    if role_name not in ["ADMINISTRADOR", "BIBLIOTECARIO"] and loan.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado a este prestamo")

    return loan
