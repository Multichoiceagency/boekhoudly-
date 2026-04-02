import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from app.database import init_db
    import app.models  # noqa: ensure all models are imported
    await init_db()
    logger.info("FiscalFlow AI API gestart - database tables ready")
    yield
    # Shutdown
    logger.info("FiscalFlow AI API gestopt")


app = FastAPI(
    title="FiscalFlow AI API",
    description="AI-powered boekhoudplatform voor Nederlandse ondernemers",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, upload, transactions, vat, ai, bank, cloud_storage, perfex, admin, workspace

app.include_router(auth.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(vat.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(bank.router, prefix="/api")
app.include_router(cloud_storage.router, prefix="/api")
app.include_router(perfex.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(workspace.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "FiscalFlow AI"}
