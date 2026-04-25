from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from api.routers import transaction, alerts, auth, feedback

# Database connection
from database import mongo

app = FastAPI(
    title="Fraud Detection System API",
    description="Backend API for Fraud Detection System",
    version="1.0.0"
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await mongo.connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await mongo.close_mongo_connection()

app.include_router(transaction.router)
app.include_router(alerts.router)
app.include_router(auth.router)
app.include_router(feedback.router)

@app.get("/", tags=["Health Check"])
async def root():
    return {
        "message": "Fraud Detection System API is running",
        "status": "healthy"
    }