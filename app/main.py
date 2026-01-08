from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.v1 import inference, auth, users
from app.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(inference.router, prefix=settings.API_V1_STR, tags=["inference"])

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

def main():
    import uvicorn
    # run with reload=True for dev
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
