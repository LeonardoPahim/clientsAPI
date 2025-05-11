import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import List, Optional
import asyncio

from app.models.client import Client as ClientModel
from app.models.product import Product as ProductRefModel
from app.schemas.product import FavoriteProductDisplay, ProductExternal
from app.services import product_service

async def add_favorite_product(db: AsyncSession, client_id: uuid.UUID, product_id: int) -> ClientModel:
    """
    Adds a product to a client's list of favorite products.

    Args:
        db: The asynchronous database session.
        client_id: The UUID of the client.
        product_id: The ID of the product to add to favorites (from external API).

    Returns:
        The updated ClientModel object with the new favorite product association.

    Raises:
        HTTPException (various, see original docstring)
    """
    client = await db.get(ClientModel, client_id, options=[selectinload(ClientModel.favorite_products)])
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    external_product_data = await product_service.get_cached_product_by_id(product_id)
    if not external_product_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id {product_id} not found in external API.")

    if any(fav_prod_ref.id == product_id for fav_prod_ref in client.favorite_products):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product already in favorites.")

    product_ref = await db.get(ProductRefModel, product_id)
    if not product_ref:
        product_ref = ProductRefModel(id=product_id)
        db.add(product_ref)

    client.favorite_products.add(product_ref)
    await db.commit()
    await db.refresh(client)
    return client

async def remove_favorite_product(db: AsyncSession, client_id: uuid.UUID, product_id: int) -> ClientModel:
    """
    Removes a product from a client's list of favorite products.

    Args:
        db: The asynchronous database session.
        client_id: The UUID of the client.
        product_id: The ID of the product to remove from favorites.

    Returns:
        The updated ClientModel object after removing the product association.

    Raises:
        HTTPException (various, see original docstring)
    """
    client = await db.get(ClientModel, client_id, options=[selectinload(ClientModel.favorite_products)])
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    product_ref_to_remove = None
    for fav_prod_ref in client.favorite_products:
        if fav_prod_ref.id == product_id:
            product_ref_to_remove = fav_prod_ref
            break

    if not product_ref_to_remove:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not in client's favorites.")

    client.favorite_products.remove(product_ref_to_remove)
    await db.commit()
    await db.refresh(client)
    return client

async def get_formatted_favorites_for_client(db: AsyncSession, client_id: uuid.UUID) -> List[FavoriteProductDisplay]:
    """
    Retrieves a list of favorite products for a given client, formatted for display.

    Args:
        db: The asynchronous database session.
        client_id: The UUID of the client whose favorites are to be retrieved.

    Returns:
        A list of FavoriteProductDisplay Pydantic schema objects.

    Raises:
        HTTPException: If the client with the given client_id is not found (status_code 404).
    """
    result = await db.execute(
        select(ClientModel)
        .options(selectinload(ClientModel.favorite_products))
        .filter(ClientModel.id == client_id)
    )
    client = result.scalars().first()

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    favorite_product_details: List[FavoriteProductDisplay] = []
    product_ids_to_fetch: List[int] = [fav_prod_ref.id for fav_prod_ref in client.favorite_products]

    if not product_ids_to_fetch:
        return []

    tasks = [product_service.get_cached_product_by_id(pid) for pid in product_ids_to_fetch]
    external_product_results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, product_data_or_exc in enumerate(external_product_results):
        if isinstance(product_data_or_exc, Exception):
            print(f"Error fetching details for product_id {product_ids_to_fetch[i]}: {product_data_or_exc}")
            continue
        
        product_data: Optional[ProductExternal] = product_data_or_exc
        if product_data:
            review_rate_value = None
            review_count_value = None
            if product_data.rating:
                review_rate_value = product_data.rating.rate
                review_count_value = product_data.rating.count

            favorite_product_details.append(
                FavoriteProductDisplay(
                    id=product_data.id,
                    title=product_data.title,
                    image=product_data.image,
                    price=product_data.price,
                    review=review_rate_value,
                    review_count=review_count_value
                )
            )
    return favorite_product_details