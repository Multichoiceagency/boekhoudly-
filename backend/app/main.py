import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, upload, transactions, vat, ai, bank, cloud_storage, perfex, admin, workspace

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FiscalFlow AI API",
    description="AI-powered boekhoudplatform voor Nederlandse ondernemers",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.on_event("startup")
async def startup():
    logger.info("FiscalFlow AI API gestart")


@app.on_event("shutdown")
async def shutdown():
    logger.info("FiscalFlow AI API gestopt")
