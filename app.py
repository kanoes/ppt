import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

load_dotenv(override=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.services.db import init_ppt_metadata_table
    await init_ppt_metadata_table()
    yield


app = FastAPI(lifespan=lifespan)

cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def include_routers():
    from src.api import routes_async

    app.include_router(routes_async.router, prefix="/api/v2", tags=["async"])


include_routers()
