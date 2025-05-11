from pydantic import BaseModel, HttpUrl
from typing import Optional

class ProductExternalRating(BaseModel):
    rate: Optional[float] = None
    count: Optional[int] = None

class ProductExternal(BaseModel):
    id: int
    title: str
    price: float
    description: Optional[str] = None
    category: Optional[str] = None
    image: Optional[HttpUrl] = None
    rating: Optional[ProductExternalRating] = None

class FavoriteProductDisplay(BaseModel):
    id: int
    title: str
    image: Optional[HttpUrl] = None
    price: float
    review: Optional[float] = None
    review_count: Optional[int] = None