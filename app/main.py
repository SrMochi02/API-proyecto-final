from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.routers import auth, users, authors, categories, books, loans


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejador de ciclo de vida de FastAPI:
    Crea las tablas en la base de datos si no existen al iniciar la aplicacion.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configuracion de CORS para admitir clientes web / frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion de routers bajo el prefijo comun API V1
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(authors.router, prefix=settings.API_V1_STR)
app.include_router(categories.router, prefix=settings.API_V1_STR)
app.include_router(books.router, prefix=settings.API_V1_STR)
app.include_router(loans.router, prefix=settings.API_V1_STR)


@app.get("/", tags=["General"], summary="Ruta raiz del servicio")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "documentation": "/docs",
        "endpoints_prefix": settings.API_V1_STR
    }


@app.get("/health", tags=["General"], summary="Verificacion de salud de la API")
def health_check():
    return {"status": "healthy"}
