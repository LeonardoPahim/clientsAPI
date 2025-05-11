from fastapi import FastAPI
from app.core.config import settings
from app.routers import auth as auth_router
from app.routers import clients as clients_router
from app.routers import favorites as favorites_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="API para gerenciar clientes e sua lista de produtos favoritos.",
    version="1.0"
)

app.include_router(auth_router.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Autenticação por token JWT"])
app.include_router(clients_router.router, prefix=settings.API_V1_STR)
app.include_router(favorites_router.router, prefix=settings.API_V1_STR)