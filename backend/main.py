from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.routers import usuarios_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # permite todo (solo desarrollo)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API primero
@app.get("/")
def root():
    return {"mensaje": "API funcionando"}

app.include_router(usuarios_router.router)

# Frontend en otra ruta
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")