import httpx
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from cachetools import TTLCache
from app.core.config import settings
from app.schemas.product import ProductExternal
from collections import defaultdict

FAKESTORE_API_PRODUCTS_URL = f"{settings.FAKESTOREAPI_URL}/products"

product_id_cache = TTLCache(maxsize=200, ttl=3600)
product_id_locks = defaultdict(asyncio.Lock)

async def _fetch_product_data_from_api(product_id: int) -> Optional[ProductExternal]:
    """Internal function to actually fetch and parse a single product from the API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{FAKESTORE_API_PRODUCTS_URL}/{product_id}")
            response.raise_for_status()
            data = response.json()
            return ProductExternal(**data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            print(f"HTTP error fetching product {product_id}: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from external product API: {e.response.text}"
            )
        except httpx.RequestError as e:
            print(f"Request error fetching product {product_id}: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="External product API is unavailable.")
        except Exception as e:
            print(f"Generic error fetching product {product_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process product data from external API. FakeStoreAPI has a limit of 20 products.")

async def get_cached_product_by_id(product_id: int) -> Optional[ProductExternal]:
    if product_id in product_id_cache:
        return product_id_cache[product_id]

    async with product_id_locks[product_id]:
        if product_id in product_id_cache:
            return product_id_cache[product_id]

        product_data = await _fetch_product_data_from_api(product_id)
        product_id_cache[product_id] = product_data
        return product_data

all_products_cache = TTLCache(maxsize=1, ttl=3600)
all_products_lock = asyncio.Lock()

async def _fetch_all_products_data_from_api() -> List[ProductExternal]:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(FAKESTORE_API_PRODUCTS_URL)
            response.raise_for_status()
            products_data = response.json()
            return [ProductExternal(**p_data) for p_data in products_data]
        except httpx.RequestError as e:
            print(f"Request error fetching all products: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="External product API is unavailable.")
        except Exception as e:
            print(f"Generic error fetching all products: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process product list from external API.")

async def get_cached_all_products() -> List[ProductExternal]:
    cache_key = "all_products_list"
    if cache_key in all_products_cache:
        return all_products_cache[cache_key]

    async with all_products_lock:
        if cache_key in all_products_cache:
            return all_products_cache[cache_key]

        products_list = await _fetch_all_products_data_from_api()
        all_products_cache[cache_key] = products_list
        return products_list