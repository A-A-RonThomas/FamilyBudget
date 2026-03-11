from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers.pages import transactions as transactions_pages, import_transactions as import_transactions_pages
from routers.api import transactions as transactions_api, import_transactions as import_transactions_api
from routers.api import budget as budget_api
from core.database import Base, engine, DB_PATH
from contextlib import asynccontextmanager
import models
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    if not os.path.exists(DB_PATH):
        Base.metadata.create_all(bind=engine)
    yield
    # shutdown (anything after yield runs on shutdown)


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(transactions_pages.router)
app.include_router(import_transactions_pages.router)

app.include_router(
    transactions_api.router,
    prefix="/api",
    tags=["Transactions API"]
)

app.include_router(
    import_transactions_api.router,
    prefix="/api",
    tags=["Import API"]
)

app.include_router(
    budget_api.router,
    prefix="/api",
    tags=["Budget API"]
)