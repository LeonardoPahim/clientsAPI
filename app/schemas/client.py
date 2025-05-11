import uuid
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from app.schemas.product import FavoriteProductDisplay

class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None

class Client(ClientBase):
    id: uuid.UUID

    class Config:
        from_attributes = True

class ClientWithFavorites(Client):
    favorites: List[FavoriteProductDisplay] = []