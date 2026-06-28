"""Entry point — starts the uvicorn server."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from core.config import config
from db.db_manager import DbManager
from api import health, generate, hints, media, options, scenarios, settings, themes, customize, test


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = DbManager(url=config.DB_URL)
    app.state.db = db
    yield
    db.engine.dispose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(generate.router)
app.include_router(hints.router)
app.include_router(media.router)
app.include_router(options.router)
app.include_router(scenarios.router)
app.include_router(settings.router)
app.include_router(themes.router)
app.include_router(customize.router)
app.include_router(test.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)
