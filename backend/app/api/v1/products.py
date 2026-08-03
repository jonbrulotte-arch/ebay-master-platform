import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import ConflictError, NotFoundError
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=PaginatedResponse[ProductListResponse])
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = None,
    category_id: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Product).where(Product.user_id == current_user.id)

    if search:
        query = query.where(
            Product.title.ilike(f"%{search}%") | Product.sku.ilike(f"%{search}%")
        )
    if category_id:
        query = query.where(Product.category_id == category_id)
    if is_active is not None:
        query = query.where(Product.is_active == is_active)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Product.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    products = result.scalars().all()

    return PaginatedResponse(
        items=[ProductListResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(Product).where(
            Product.user_id == current_user.id, Product.sku == product_in.sku
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"Product with SKU '{product_in.sku}' already exists")

    product = Product(user_id=current_user.id, **product_in.model_dump())
    db.add(product)
    await db.flush()

    inventory = Inventory(product_id=product.id, quantity_available=0)
    db.add(inventory)
    await db.flush()

    await db.refresh(product, ["images"])
    return product


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.images))
        .where(Product.id == product_id, Product.user_id == current_user.id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    product_in: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.images))
        .where(Product.id == product_id, Product.user_id == current_user.id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("Product not found")

    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.flush()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.user_id == current_user.id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("Product not found")

    await db.delete(product)
