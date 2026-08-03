from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(db: AsyncSession, query: Select, page: int, page_size: int) -> tuple:
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    items_query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(items_query)
    items = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size
    return items, total, total_pages
