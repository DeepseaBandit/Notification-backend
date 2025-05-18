from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.e_notif import router as email_router
from services.sms_notif import router as sms_router
from services.in_notif import router as inapp_router
import os

app = FastAPI()

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://notification-app-dgdx.vercel.app") 
DEVELOPMENT_URL = os.getenv("DEVELOPMENT_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, DEVELOPMENT_URL, "*"],  # Temporarily include "*" during debugging
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "X-Requested-With", "Accept", "Authorization", "Access-Control-Allow-Origin"],
)

app.include_router(email_router, prefix="/email", tags=["Email"])
app.include_router(sms_router, prefix="/sms", tags=["SMS"])
app.include_router(inapp_router, prefix="/inapp", tags=["In-App"])

@app.get("/")
async def root():
    """Root endpoint for API health check"""
    return {
        "message": "Notification API is running",
        "environment": "production" if os.getenv("VERCEL_ENV") else "development",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": "production" if os.getenv("VERCEL_ENV") else "development"
    }

@app.get("/api/environment")
async def environment():
    """Debug endpoint to check environment variables"""
    return {
        "environment": os.getenv("VERCEL_ENV", "development"),
        "frontend_url": FRONTEND_URL,
        "is_vercel": os.getenv("VERCEL") == "1"
    }
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))  
    uvicorn.run("main:app", host="0.0.0.0", port=port)
