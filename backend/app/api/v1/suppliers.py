import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.product_supplier import ProductSupplier
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.supplier import (
    ProductSupplierCreate,
    ProductSupplierResponse,
    ProductSupplierUpdate,
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
)

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=PaginatedResponse[SupplierResponse])
async def list_suppliers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    platform: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Supplier).where(Supplier.user_id == current_user.id)
    if platform:
        query = query.where(Supplier.platform == platform)
    if is_active is not None:
        query = query.where(Supplier.is_active == is_active)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Supplier.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    suppliers = result.scalars().all()

    return PaginatedResponse(
        items=[SupplierResponse.model_validate(s) for s in suppliers],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    supplier_in: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    supplier = Supplier(user_id=current_user.id, **supplier_in.model_dump())
    db.add(supplier)
    await db.flush()
    await db.refresh(supplier)
    return supplier


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id, Supplier.user_id == current_user.id)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise NotFoundError("Supplier not found")
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: uuid.UUID,
    supplier_in: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id, Supplier.user_id == current_user.id)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise NotFoundError("Supplier not found")

    for field, value in supplier_in.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    await db.flush()
    await db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}", status_code=204)
async def delete_supplier(
    supplier_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id, Supplier.user_id == current_user.id)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise NotFoundError("Supplier not found")
    await db.delete(supplier)


# --- Product-Supplier linking ---


@router.get(
    "/products/{product_id}/suppliers",
    response_model=list[ProductSupplierResponse],
    tags=["products"],
)
async def list_product_suppliers(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProductSupplier).where(ProductSupplier.product_id == product_id)
    )
    return result.scalars().all()


@router.post(
    "/products/{product_id}/suppliers",
    response_model=ProductSupplierResponse,
    status_code=201,
    tags=["products"],
)
async def link_product_supplier(
    product_id: uuid.UUID,
    link_in: ProductSupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = ProductSupplier(product_id=product_id, **link_in.model_dump())
    db.add(link)
    await db.flush()
    await db.refresh(link)
    return link


@router.put(
    "/products/{product_id}/suppliers/{supplier_id}",
    response_model=ProductSupplierResponse,
    tags=["products"],
)
async def update_product_supplier(
    product_id: uuid.UUID,
    supplier_id: uuid.UUID,
    link_in: ProductSupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProductSupplier).where(
            ProductSupplier.product_id == product_id,
            ProductSupplier.supplier_id == supplier_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise NotFoundError("Product-supplier link not found")

    for field, value in link_in.model_dump(exclude_unset=True).items():
        setattr(link, field, value)
    await db.flush()
    await db.refresh(link)
    return link
