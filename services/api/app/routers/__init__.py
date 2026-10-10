# # # from fastapi import APIRouter

# # # from app.routers import chat, dataset, health, learning, models, predict

# # # api_router = APIRouter()

# # # for module in (health, dataset, models, predict, learning, chat):
# # #     api_router.include_router(module.router)

# # from fastapi import APIRouter, Depends

# # from app.deps import get_current_user, require_admin
# # from app.routers import admin, auth, chat, dataset, health, learning, models, predict

# # api_router = APIRouter()

# # # public
# # for module in (health, auth):
# #     api_router.include_router(module.router)

# # # any logged-in user
# # for module in (dataset, models, predict, chat):
# #     api_router.include_router(module.router, dependencies=[Depends(get_current_user)])

# # # administrators only
# # for module in (learning, admin):
# #     api_router.include_router(module.router, dependencies=[Depends(require_admin)])


# from fastapi import APIRouter, Depends

# from app.deps import get_current_user, require_admin
# from app.routers import admin, admin_data, auth, chat, dataset, health, history, learning, models, predict

# api_router = APIRouter()

# # public
# for module in (health, auth):
#     api_router.include_router(module.router)

# # any logged-in user
# for module in (dataset, models, predict, chat, history):
#     api_router.include_router(module.router, dependencies=[Depends(get_current_user)])

# # administrators only
# for module in (learning, admin, admin_data):
#     api_router.include_router(module.router, dependencies=[Depends(require_admin)])

from fastapi import APIRouter, Depends

from app.deps import get_current_user, require_admin
from app.routers import (
    admin, admin_data, admin_learning, admin_stats, auth, chat, dataset, health, history, learning, models, predict, reviews,
)

api_router = APIRouter()

# public
for module in (health, auth):
    api_router.include_router(module.router)

# any logged-in user
for module in (dataset, models, predict, chat, history, reviews, learning):
    api_router.include_router(module.router, dependencies=[Depends(get_current_user)])

# administrators only
for module in (admin, admin_data, admin_stats, admin_learning):
    api_router.include_router(module.router, dependencies=[Depends(require_admin)])