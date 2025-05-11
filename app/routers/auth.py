from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.token import Token
from app.schemas.auth import MasterLoginRequest
from app.core.security import create_access_token, verify_password
from app.core.config import settings

router = APIRouter()

@router.post("/master-token", response_model=Token, summary="Gera token de acesso do administrador")
async def master_login_for_access_token(
    form_data: MasterLoginRequest,
):
    """
    Autentica o login do administrador e retorna um token JWT de acesso para os demais endpoints.

    username: favorite_products_admin
    password: favorite_procusts_password

    Retorna:
    Um objeto de token com o token e o tipo (Bearer).

    """
    if form_data.username != settings.MASTER_USERNAME or \
       not verify_password(form_data.password, settings.MASTER_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    admin_access_token = create_access_token(
        data={"sub": settings.MASTER_USERNAME, "role": "master"}
    )
    return {"access_token": admin_access_token, "token_type": "bearer"}