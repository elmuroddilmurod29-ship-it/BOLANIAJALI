from aiogram import Router
from .user import router as user_router
from .payment import router as payment_router
from .admin import router as admin_router

main_router = Router()
main_router.include_router(admin_router)
main_router.include_router(payment_router)
main_router.include_router(user_router)

__all__ = ["main_router", "user_router", "payment_router", "admin_router"]
