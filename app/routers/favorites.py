import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.crud import favorite as crud_favorite
from app.schemas.client import ClientWithFavorites
from app.schemas.product import FavoriteProductDisplay
from app.core.database import get_db
from app.core.security import get_current_admin_user

router = APIRouter(
    prefix="/clients/{client_id}/favorites",
    tags=["Gerenciamento da lista de produtos favoritos"],
    dependencies=[Depends(get_current_admin_user)]
)

@router.post("/{product_id}", response_model=ClientWithFavorites, status_code=status.HTTP_201_CREATED, summary="Adiciona um produto à lista de favoritos de um cliente")
async def admin_add_product_to_favorites(
    client_id: uuid.UUID = Path(..., description="The UUID of the client"),
    product_id: int = Path(..., description="The ID of the product to add to favorites"),
    db: AsyncSession = Depends(get_db),
):
    """
    Adiciona um produto à lista de favoritos de um cliente existente.

    Argumentos:
        client_id: UUID do cliente
        product_id: ID do produto da API externa (um inteiro no caso da FakeStoreAPI)

    Retorna:
        201 = Um objeto ClientWithFavorites, um cliente com todas informações e sua lista de favoritos
        404 = Cliente ou produto externo não existe
        400 = Produto já está presente na lista de favoritos do cliente
    """
    try:
        updated_client_model = await crud_favorite.add_favorite_product(db=db, client_id=client_id, product_id=product_id)
    except HTTPException as e:
        raise e

    favorites_list = await crud_favorite.get_formatted_favorites_for_client(db=db, client_id=updated_client_model.id)
    from app.schemas.client import Client as ClientSchema
    client_schema_data = ClientSchema.model_validate(updated_client_model)
    return ClientWithFavorites(**client_schema_data.model_dump(), favorites=favorites_list)

@router.delete("/{product_id}", response_model=ClientWithFavorites, summary="Deleta um produto da lista de favoritos do cliente")
async def admin_remove_product_from_favorites(
    client_id: uuid.UUID = Path(..., description="The UUID of the client"),
    product_id: int = Path(..., description="The ID of the product to remove from favorites"),
    db: AsyncSession = Depends(get_db),
):
    """
    Deleta um produto da lista de favoritos de um cliente.

    Argumentos:
        client_id: UUID do cliente
        product_id: ID do produto da API externa (um inteiro no caso da FakeStoreAPI)

    Retorna:
        200 = Um objeto ClientWithFavorites atualizado
        404 = Cliente não encontrado ou produto não está na lista do cliente
    """
    try:
        updated_client_model = await crud_favorite.remove_favorite_product(db=db, client_id=client_id, product_id=product_id)
    except HTTPException as e:
        raise e

    favorites_list = await crud_favorite.get_formatted_favorites_for_client(db=db, client_id=updated_client_model.id)
    from app.schemas.client import Client as ClientSchema
    client_schema_data = ClientSchema.model_validate(updated_client_model)
    return ClientWithFavorites(**client_schema_data.model_dump(), favorites=favorites_list)

@router.get("/", response_model=List[FavoriteProductDisplay], summary="Retorna uma lista de favoritos de um cliente")
async def admin_list_client_favorites(
    client_id: uuid.UUID = Path(..., description="The UUID of the client"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna uma lista de produtos favoritos de um cliente específico.

    Argumentos:
        client_id: UUID do cliente

    Retorna:
        200 = Uma lista de objetos FavoriteProductDisplay, contendo os detalhes de cada produto.
        404 = Cliente não existe
    """
    try:
        return await crud_favorite.get_formatted_favorites_for_client(db=db, client_id=client_id)
    except HTTPException as e:
        raise e