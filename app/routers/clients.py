import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.crud import client as crud_client
from app.crud import favorite as crud_favorite
from app.schemas.client import Client, ClientCreate, ClientUpdate, ClientWithFavorites
from app.core.database import get_db
from app.core.security import get_current_admin_user

router = APIRouter(
    prefix="/clients",
    tags=["Gerenciamento de Clientes"],
    dependencies=[Depends(get_current_admin_user)]
)

@router.post("/", response_model=Client, status_code=status.HTTP_201_CREATED, summary="Cria um novo cliente")
async def admin_create_client(
    client_in: ClientCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Cria um novo cliente.

    Argumentos:
        name: Nome do cliente
        email: Email do cliente, não aceitando emails já cadastrados.

    Retorna:
        201 = O objeto Client criado, junto de seu UUID autogerado.
        422 = Erro de validação nos campos
    """
    return await crud_client.create_client(db=db, client_in=client_in)


@router.get("/", response_model=List[Client], summary="Lista todos clientes cadastrados")
async def admin_read_clients(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna uma lista de todos clientes, utilizando paginação.

    Argumentos:
        skip: Ignora uma quantidade de N clientes
        limit: Limita a quantidade de clientes da lista retornada

    Retorna:
        200 = Lista de objetos Client. Não incluí os favoritos.
        422 = Erro de validação nos campos
    """
    return await crud_client.get_clients(db, skip=skip, limit=limit)


@router.get("/{client_id}", response_model=ClientWithFavorites, summary="Retorna todas informações de um cliente")
async def admin_read_client(
    client_id: uuid.UUID = Path(..., description="The UUID of the client to retrieve"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna todas informações de um cliente específico, incluindo a lista de produtos favoritos.

    Argumentos:
        client_id: o UUID do cliente

    Retorna:
        200 = Um objeto ClientWithFavorites, que consiste nas informações do cliente e sua lista de produtos favoritos.
        422 = Erro de validação nos campos
    """
    db_client = await crud_client.get_client(db, client_id=client_id)
    if db_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    favorites_list = await crud_favorite.get_formatted_favorites_for_client(db=db, client_id=client_id)
    client_schema_data = Client.model_validate(db_client)
    return ClientWithFavorites(**client_schema_data.model_dump(), favorites=favorites_list)


@router.put("/{client_id}", response_model=Client, summary="Atualiza as informações de um cliente")
async def admin_update_client(
    client_id: uuid.UUID,
    client_in: ClientUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Atualiza as informações de um cliente existente.

    Argumentos:
        client_id: UUID do cliente à ser atualizado
        body: name e email do cliente à ser atualizado

    Retorna:

        200 = O objeto Client atualizado
        404 = Cliente com esse UUID não existe
        400 = Email já registrado
    """
    updated_client = await crud_client.update_client(db=db, client_id=client_id, client_in=client_in)
    if updated_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found to update")
    return updated_client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deleta um cliente")
async def admin_delete_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Deleta um cliente

    Argumentos:
        client_id: UUID do cliente à ser deletado
    
    Retorna:
        204 = Deletou com sucesso
    """
    deleted_client = await crud_client.delete_client(db=db, client_id=client_id)
    if deleted_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found to delete")
    return None