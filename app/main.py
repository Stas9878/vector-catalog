from pathlib import Path
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes import catalog, search
from app.settings import get_settings
from app.qdrant.client import get_qdrant_client

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.qdrant = get_qdrant_client()
    app.state.templates = templates
    try:
        yield
    finally:
        await app.state.qdrant.close()


app = FastAPI(title="VectorCatalog", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(catalog.router)
app.include_router(search.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "env": get_settings().APP_ENV}
