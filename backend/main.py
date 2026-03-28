import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from routers import zipcode
from services import ken_all

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    data_dir = os.environ.get("DATA_DIR", "data")
    ken_all.load(data_dir)
    yield


app = FastAPI(
    title="はがき配布サービス バックエンドAPI",
    version="1.0",
    lifespan=lifespan,
)

app.include_router(zipcode.router)
