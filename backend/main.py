import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from routers import address, zipcode
from services import jigyosyo, ken_all

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    data_dir = os.environ.get("DATA_DIR", "data")
    ken_all.load(data_dir)
    jigyosyo.load(data_dir)
    yield


app = FastAPI(
    title="はがき配布サービス バックエンドAPI",
    version="2.1",
    lifespan=lifespan,
)

app.include_router(zipcode.router)
app.include_router(address.router)
