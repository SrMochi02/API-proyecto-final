"""
Script de inicializacion de datos base (Seeder) para demostracion y pruebas.
Crea roles por defecto, usuarios de prueba (Admin, Bibliotecario, Usuario),
autores, categorias y libros iniciales.
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User
from app.models.author import Author
from app.models.category import Category
from app.models.book import Book


def seed_database():
    print("[+] Inicializando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Crear Roles del sistema
        print("[+] Creando roles predeterminados...")
        roles_data = [
            {"name": "ADMINISTRADOR", "description": "Acceso total y administracion del sistema"},
            {"name": "BIBLIOTECARIO", "description": "Gestion de catalogo, prestamos y devoluciones"},
            {"name": "USUARIO", "description": "Consulta de catalogo y solicitud de prestamos personales"}
        ]
        roles_map = {}
        for r_data in roles_data:
            role = db.query(Role).filter(Role.name == r_data["name"]).first()
            if not role:
                role = Role(name=r_data["name"], description=r_data["description"])
                db.add(role)
                db.commit()
                db.refresh(role)
            roles_map[role.name] = role

        # 2. Crear Usuarios de prueba
        print("[+] Creando usuarios iniciales...")
        users_data = [
            {
                "username": "admin",
                "email": "admin@biblioteca.edu",
                "full_name": "Administrador General",
                "password": "adminpassword123",
                "role_id": roles_map["ADMINISTRADOR"].id
            },
            {
                "username": "bibliotecario",
                "email": "bibliotecario@biblioteca.edu",
                "full_name": "Bibliotecario Encargado",
                "password": "bibliopassword123",
                "role_id": roles_map["BIBLIOTECARIO"].id
            },
            {
                "username": "estudiante",
                "email": "estudiante@biblioteca.edu",
                "full_name": "Estudiante Lector",
                "password": "studentpassword123",
                "role_id": roles_map["USUARIO"].id
            }
        ]
        for u_data in users_data:
            existing = db.query(User).filter(User.username == u_data["username"]).first()
            if not existing:
                user = User(
                    username=u_data["username"],
                    email=u_data["email"],
                    full_name=u_data["full_name"],
                    hashed_password=get_password_hash(u_data["password"]),
                    role_id=u_data["role_id"],
                    is_active=True
                )
                db.add(user)
        db.commit()

        # 3. Crear Autores
        print("[+] Registrando autores literarios...")
        autores_data = [
            {"nombre": "Gabriel Garcia Marquez", "nacionalidad": "Colombiana", "biografia": "Premio Nobel de Literatura 1982."},
            {"nombre": "Jorge Luis Borges", "nacionalidad": "Argentina", "biografia": "Maestro del relato fantastico y la poesia."},
            {"nombre": "Isabel Allende", "nacionalidad": "Chilena", "biografia": "Destacada escritora de novelas hispanoamericanas."}
        ]
        autores_map = {}
        for a_data in autores_data:
            autor = db.query(Author).filter(Author.nombre == a_data["nombre"]).first()
            if not autor:
                autor = Author(**a_data)
                db.add(autor)
                db.commit()
                db.refresh(autor)
            autores_map[autor.nombre] = autor

        # 4. Crear Categorias
        print("[+] Registrando categorias...")
        categorias_data = [
            {"nombre": "Novela", "descripcion": "Obras literarias de ficcion en prosa"},
            {"nombre": "Realismo Magico", "descripcion": "Elementos magicos percibidos como reales"},
            {"nombre": "Ensayo", "descripcion": "Textos reflexivos y academicos"}
        ]
        categorias_map = {}
        for c_data in categorias_data:
            cat = db.query(Category).filter(Category.nombre == c_data["nombre"]).first()
            if not cat:
                cat = Category(**c_data)
                db.add(cat)
                db.commit()
                db.refresh(cat)
            categorias_map[cat.nombre] = cat

        # 5. Crear Libros iniciales
        print("[+] Registrando libros en catalogo...")
        libros_data = [
            {
                "titulo": "Cien años de soledad",
                "isbn": "978-0307474728",
                "anio_publicacion": 1967,
                "autor_id": autores_map["Gabriel Garcia Marquez"].id,
                "categoria_id": categorias_map["Realismo Magico"].id,
                "ejemplares_totales": 3,
                "ejemplares_disponibles": 3,
                "disponible": True
            },
            {
                "titulo": "Ficciones",
                "isbn": "978-8420633121",
                "anio_publicacion": 1944,
                "autor_id": autores_map["Jorge Luis Borges"].id,
                "categoria_id": categorias_map["Novela"].id,
                "ejemplares_totales": 1,
                "ejemplares_disponibles": 1,
                "disponible": True
            },
            {
                "titulo": "La casa de los espiritus",
                "isbn": "978-0525433484",
                "anio_publicacion": 1982,
                "autor_id": autores_map["Isabel Allende"].id,
                "categoria_id": categorias_map["Novela"].id,
                "ejemplares_totales": 2,
                "ejemplares_disponibles": 2,
                "disponible": True
            }
        ]
        for l_data in libros_data:
            existing = db.query(Book).filter(Book.isbn == l_data["isbn"]).first()
            if not existing:
                book = Book(**l_data)
                db.add(book)
        db.commit()

        print("[+] Base de datos inicializada exitosamente.")

    except Exception as e:
        db.rollback()
        print(f"[-] Error poblando base de datos: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
