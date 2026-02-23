from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.generate_review import router as review_router
from app.routes.admin_data import router as admin_data_router
from app.routes.public_client import router as public_client_router
from app.routes.qr_stats import router as qr_stats_router
from app.routes.qr_token import router as qr_token_router
from app.routes.public_qr import router as public_qr_router
from app.routes.qr_admin import router as qr_admin_router
from app.routes.public_token import router as public_token_router

app = FastAPI(title="GMB Lite AI Backend")

# ✅ CORS (DEV + PROD SAFE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev
        "http://localhost:3000",
        "https://kodeverse.online" # Production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ ROUTES (ORDER SAFE)
app.include_router(review_router, prefix="/api")
app.include_router(admin_data_router)
app.include_router(public_client_router)
app.include_router(qr_stats_router)
app.include_router(qr_token_router)
app.include_router(public_qr_router)
app.include_router(qr_admin_router)
app.include_router(public_token_router)

@app.get("/")
def health():
    return {"status": "Backend running"}