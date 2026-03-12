from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from app.routers import transaction, alerts, auth, feedback

# Database connection
from app.db.mongo import connect_to_mongo, close_mongo_connection


# ---------------------------------------------------
# Create FastAPI Application
# ---------------------------------------------------
app = FastAPI(
    title="Intelligent Fraud Detection System API",
    description="Backend API for Fraud Detection System",
    version="1.0.0"
)


# ---------------------------------------------------
# CORS Configuration (for frontend integration)
# ---------------------------------------------------
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to origins list in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------
# Database Startup Event
# ---------------------------------------------------
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()


# ---------------------------------------------------
# Database Shutdown Event
# ---------------------------------------------------
@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()


# ---------------------------------------------------
# Include Routers
# ---------------------------------------------------
app.include_router(transaction.router)
app.include_router(alerts.router)
app.include_router(auth.router)
app.include_router(feedback.router)


# ---------------------------------------------------
# Root Endpoint
# ---------------------------------------------------
@app.get("/", tags=["Health Check"])
async def root():
    return {
        "message": "Fraud Detection System API is running",
        "status": "healthy"
    }