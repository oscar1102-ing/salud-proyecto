from fastapi import APIRouter, HTTPException
from backend.services import usuario_service
from backend.models.usuario_model import UsuarioRegistro, LoginData
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/.well-known/appspecific/com.chrome.devtools.json")
def devtools():
    return JSONResponse(content={})

@router.post("/api/registro")
def registrar_usuario(datos: UsuarioRegistro):
    resultado = usuario_service.registrar_usuario(datos)
    
    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    
    return resultado


@router.post("/api/login")
def login(data: LoginData):
    return usuario_service.login_usuario(data)

@router.get("/perfil/{usuario_id}")
def obtener_perfil(usuario_id: int):
    from repositories import perfil_repository
    perfil = perfil_repository.obtener_perfil_completo(usuario_id)
    
    if not perfil:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return perfil