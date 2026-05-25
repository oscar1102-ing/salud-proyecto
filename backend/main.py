from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.routers import usuarios_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API con prefijo /api
app.include_router(usuarios_router.router, prefix="/api")

# Frontend estático
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
