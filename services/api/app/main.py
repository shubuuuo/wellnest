# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from app.core.config import API_PREFIX, get_settings
# from app.core.errors import register_error_handlers
# from app.routers import api_router


# def create_app() -> FastAPI:
#     settings = get_settings()
#     app = FastAPI(title=settings.app_name, version="0.1.0")
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=settings.cors_origin_list,
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
#     register_error_handlers(app)
#     app.include_router(api_router, prefix=API_PREFIX)
#     return app


# app = create_app()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import API_PREFIX, get_settings
from app.core.errors import register_error_handlers
from app.routers import api_router
from app.services.seed import ensure_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_admin()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(api_router, prefix=API_PREFIX)
    return app


app = create_app()