"""Application entry point for the presentation generator service."""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def _configure_paths() -> None:
    """Ensure package subdirectories are importable when running locally."""

    base_dir = Path(__file__).resolve().parent
    # Add project root to sys.path so 'shared' module can be imported
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))


_configure_paths()

load_dotenv(override=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from shared.db.db import init_ppt_metadata_table
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
    from shared.api import routes_async

    app.include_router(routes_async.router, prefix="/api/v2", tags=["async"])


include_routers()
