from fastapi import APIRouter, HTTPException
from backend.services import usuario_service
from backend.models.usuario_model import UsuarioRegistro, LoginData
from fastapi.responses import JSONResponse
from backend.repositories import actividades_repository 
from backend.repositories import perfil_repository
from backend.services import estres_service
from backend.services import gemini_service
from datetime import datetime, timedelta

router = APIRouter()



@router.get("/estres/{usuario_id}")
def obtener_estres(usuario_id: int):
    perfil      = perfil_repository.obtener_perfil_completo(usuario_id)
    actividades = actividades_repository.obtener_actividades(usuario_id)

    if not perfil:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # actividades puede ser lista vacía, eso está bien
    resultado = estres_service.calcular_fase_estres(
        dict(perfil),
        [dict(a) for a in actividades]
    )
    return resultado

@router.get("/.well-known/appspecific/com.chrome.devtools.json")
def devtools():
    return JSONResponse(content={})

@router.post("/registro")
def registrar_usuario(datos: UsuarioRegistro):
    resultado = usuario_service.registrar_usuario(datos)
    
    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    
    return resultado


@router.post("/login")
def login(data: LoginData):
    return usuario_service.login_usuario(data)

@router.get("/perfil/{usuario_id}")
def obtener_perfil(usuario_id: int):
    perfil = perfil_repository.obtener_perfil_completo(usuario_id)
    
    if not perfil:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return perfil
    
@router.put("/perfil/{usuario_id}")
def actualizar_perfil(usuario_id: int, datos: dict):
    resultado = perfil_repository.actualizar_perfil(usuario_id, datos)
    return resultado

from backend.repositories import actividades_repository

@router.get("/actividades/{usuario_id}")
def obtener_actividades(usuario_id: int):
    actividades = actividades_repository.obtener_actividades(usuario_id)
    return actividades

@router.post("/actividades/{usuario_id}")
def crear_actividad(usuario_id: int, datos: dict):
    actividad = actividades_repository.crear_actividad(usuario_id, datos)
    return actividad

@router.delete("/actividades/{actividad_id}/{usuario_id}")
def eliminar_actividad(actividad_id: int, usuario_id: int):
    return actividades_repository.eliminar_actividad(actividad_id, usuario_id)

@router.put("/actividades/{actividad_id}/{usuario_id}/estado")
def actualizar_estado(actividad_id: int, usuario_id: int, datos: dict):
    return actividades_repository.actualizar_estado(actividad_id, usuario_id, datos["estado"])
    
@router.put("/actividades/{actividad_id}/{usuario_id}/iniciar")
def iniciar_actividad(actividad_id: int, usuario_id: int):
    resultado = actividades_repository.iniciar_actividad(actividad_id, usuario_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return resultado

@router.get("/actividades/{usuario_id}/en-curso")
def actividad_en_curso(usuario_id: int):
    actividad = actividades_repository.obtener_actividad_en_curso(usuario_id)
    if not actividad:
        return {"en_curso": False}
    return {
        "en_curso": True,
        "id": actividad["id"],
        "nombre": actividad["nombre"],
        "duracion": actividad["duracion"],
        "hora_inicio": actividad["hora_inicio"].isoformat(),
        "categoria": actividad["categoria"]
    }
    
@router.put("/actividades/{actividad_id}/{usuario_id}/pausar")
def pausar_actividad(actividad_id: int, usuario_id: int):
    resultado = actividades_repository.pausar_actividad(actividad_id, usuario_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return resultado

@router.put("/actividades/{actividad_id}/{usuario_id}/reanudar")
def reanudar_actividad(actividad_id: int, usuario_id: int):
    resultado = actividades_repository.reanudar_actividad(actividad_id, usuario_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="No hay pausa activa")
    return resultado

@router.put("/actividades/{actividad_id}/{usuario_id}/finalizar")
def finalizar_actividad(actividad_id: int, usuario_id: int, datos: dict):
    resultado = actividades_repository.finalizar_actividad(
        actividad_id, usuario_id,
        datos.get("estado", "Completada"),
        datos.get("notas")
    )
    if not resultado:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return resultado

@router.get("/actividades/{actividad_id}/{usuario_id}/historial")
def historial_actividad(actividad_id: int, usuario_id: int):
    resultado = actividades_repository.obtener_historial_actividad(actividad_id, usuario_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return resultado

@router.get("/actividades/{usuario_id}/historial")
def historial_usuario(usuario_id: int):
    return actividades_repository.obtener_historial_usuario(usuario_id)
    
@router.get("/gemini/analisis/{usuario_id}")
def analisis_gemini(usuario_id: int):
    perfil = perfil_repository.obtener_perfil_completo(usuario_id)
    if not perfil:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Actividades de hoy
    todas = actividades_repository.obtener_actividades(usuario_id)
    hoy = datetime.now().strftime("%Y-%m-%d")
    actividades_hoy = [dict(a) for a in todas if str(a["fecha"]) == hoy]

    # Historial últimos 7 días
    historial = actividades_repository.obtener_historial_usuario(usuario_id)
    hace_7_dias = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    historial_reciente = [
        dict(a) for a in historial
        if str(a["fecha"]) >= hace_7_dias
    ]

    # Calcular fase con el servicio existente
    fase_data = estres_service.calcular_fase_estres(
        dict(perfil),
        [dict(a) for a in todas]
    )

    # Obtener recomendaciones de Gemini
    gemini_data = gemini_service.analizar_usuario(
        dict(perfil),
        actividades_hoy,
        historial_reciente
    )

    # Combinar todo
    return {
        "fase": fase_data["fase"],
        "puntos": fase_data["puntos"],
        "color": fase_data["color"],
        "porcentaje": fase_data["porcentaje"],
        "recomendaciones": gemini_data["recomendaciones"] if gemini_data["exito"] else fase_data["recomendaciones"],
        "resumen": gemini_data.get("resumen", ""),
        "ia_activa": gemini_data["exito"]
    }
