from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers.pages import (transactions as transactions_pages,
                           import_transactions as import_transactions_pages,
                           budget as budget_pages)
from routers.api import transactions as transactions_api, import_transactions as import_transactions_api
from routers.api import budget as budget_api
from routers.api import simplefin
from routers.pages import settings as settings_pages
from routers.api import accounts as accounts_api
from routers.pages import visualizations as visualizations_pages
from routers.api import charts as charts_api
from routers.api import notifications as notifications_api
from core.database import Base, engine, DB_PATH
from contextlib import asynccontextmanager
from models.database import *
import os



@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    # if not os.path.exists(DB_PATH):
    Base.metadata.create_all(bind=engine)
    yield
    # shutdown (anything after yield runs on shutdown)


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(transactions_pages.router)
app.include_router(import_transactions_pages.router)
app.include_router(budget_pages.router)
app.include_router(visualizations_pages.router)
app.include_router(simplefin.router, prefix="/api", tags=["SimpleFIN API"])
app.include_router(settings_pages.router)
app.include_router(accounts_api.router, prefix="/api", tags=["Accounts API"])
app.include_router(charts_api.router, prefix="/api", tags=["Charts API"])
app.include_router(notifications_api.router, prefix="/api", tags=["Notifications API"])


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

