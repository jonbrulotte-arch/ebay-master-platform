from fastapi import APIRouter

from app.api.v1 import auth, ebay, inventory, listings, notifications, orders, pricing, products, suppliers

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(suppliers.router)
api_router.include_router(inventory.router)
api_router.include_router(listings.router)
api_router.include_router(orders.router)
api_router.include_router(pricing.router)
api_router.include_router(notifications.router)
api_router.include_router(ebay.router)
