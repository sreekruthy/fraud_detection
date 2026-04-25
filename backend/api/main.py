from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from api.routers import transaction, alerts, auth, feedback

# Database connection
from database.mongo import connect_to_mongo, close_mongo_connection


# ---------------------------------------------------
# Create FastAPI Application
# ---------------------------------------------------
app = FastAPI(
    title="Intelligent Fraud Detection System API",
    description="Backend API for Fraud Detection System",
    version="1.0.0"
)


# ---------------------------------------------------
# CORS Configuration (for frontend)
# ---------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all (OK for development)
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
# Include Routers (IMPORTANT: prefixes added)
# ---------------------------------------------------
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(transaction.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])


# ---------------------------------------------------
# Root Endpoint
# ---------------------------------------------------
@app.get("/", tags=["Health Check"])
async def root():
    return {
        "message": "Fraud Detection System API is running",
        "status": "healthy"
    }