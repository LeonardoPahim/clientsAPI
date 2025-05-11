import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from typing import Optional, List

from app.models.client import Client as ClientModel
from app.schemas.client import ClientCreate, ClientUpdate

async def get_client(db: AsyncSession, client_id: uuid.UUID) -> Optional[ClientModel]:
    result = await db.execute(select(ClientModel).filter(ClientModel.id == client_id))
    return result.scalars().first()

async def get_client_by_email(db: AsyncSession, email: str) -> Optional[ClientModel]:
    result = await db.execute(select(ClientModel).filter(ClientModel.email == email))
    return result.scalars().first()

async def get_clients(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ClientModel]:
    result = await db.execute(select(ClientModel).offset(skip).limit(limit))
    return result.scalars().all()

async def create_client(db: AsyncSession, client_in: ClientCreate) -> ClientModel:
    existing_client = await get_client_by_email(db, email=client_in.email)
    if existing_client:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")


    db_client = ClientModel(
        name=client_in.name,
        email=client_in.email
    )
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return db_client

async def update_client(db: AsyncSession, client_id: uuid.UUID, client_in: ClientUpdate) -> Optional[ClientModel]:
    db_client = await get_client(db, client_id)
    if not db_client:
        return None

    update_data = client_in.model_dump(exclude_unset=True)
    if "email" in update_data and update_data["email"] != db_client.email:
        existing_client_by_new_email = await get_client_by_email(db, email=update_data["email"])
        if existing_client_by_new_email and existing_client_by_new_email.id != client_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email already registered by another user.")

    for key, value in update_data.items():
        setattr(db_client, key, value)

    await db.commit()
    await db.refresh(db_client)
    return db_client

async def delete_client(db: AsyncSession, client_id: uuid.UUID) -> Optional[ClientModel]:
    db_client = await get_client(db, client_id)
    if not db_client:
        return None
    await db.delete(db_client)
    await db.commit()
    return db_client