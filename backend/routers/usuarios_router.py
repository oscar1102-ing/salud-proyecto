from fastapi import APIRouter, HTTPException
from backend.services import usuario_service
from backend.models.usuario_model import UsuarioRegistro, LoginData
from fastapi.responses import JSONResponse
from backend.repositories import actividades_repository 
from backend.repositories import perfil_repository
from backend.services import estres_service
from backend.services import gemini_service
from datetime import datetime, timedelta
from backend.repositories import encuesta_repository
from backend.services import email_service
from backend.repositories import mfa_repository
from backend.repositories import usuario_repository as repo
import threading

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

import threading

@router.post("/registro")
def registrar_usuario(datos: UsuarioRegistro):
    resultado = usuario_service.registrar_usuario(datos)
    
    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    
    # Enviar correo en hilo separado para no bloquear
    usuario_id = resultado["usuario"]["id"]
    email      = datos.email

    def enviar_en_background():
        from backend.services.email_service import generar_codigo, enviar_codigo
        codigo = generar_codigo()
        mfa_repository.guardar_codigo(usuario_id, codigo, "registro")
        enviar_codigo(email, codigo, "registro")

    hilo = threading.Thread(target=enviar_en_background)
    hilo.daemon = True
    hilo.start()

    return {**resultado, "usuario_id": usuario_id}
    

@router.post("/login")
def login(data: LoginData):
    resultado = usuario_service.login_usuario(data)
    
    usuario_raw = repo.buscar_por_email(data.email)
    
    if not usuario_raw.get("verificado"):
        raise HTTPException(
            status_code=403,
            detail="Cuenta no verificada. Revisa tu correo.",
            headers={"X-Usuario-Id": str(usuario_raw["id"])}
        )
    
    return resultado

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

    todas = actividades_repository.obtener_actividades(usuario_id)
    fase_data = estres_service.calcular_fase_estres(
        dict(perfil), [dict(a) for a in todas]
    )

    cache = gemini_service.obtener_cache(usuario_id)
    if cache:
        print(f"Usando caché para usuario {usuario_id}")
        return {
            "fase": fase_data["fase"],
            "puntos": fase_data["puntos"],
            "color": fase_data["color"],
            "porcentaje": fase_data["porcentaje"],
            "recomendaciones": cache.get("recomendaciones", []),
            "resumen": cache.get("resumen", ""),
            "ia_activa": True,
            "desde_cache": True
        }

    print(f"Llamando a Gemini para usuario {usuario_id}")
    hoy = datetime.now().strftime("%Y-%m-%d")
    actividades_hoy = [dict(a) for a in todas if str(a["fecha"]) == hoy]

    historial = actividades_repository.obtener_historial_usuario(usuario_id)
    hace_7_dias = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    historial_reciente = [
        dict(a) for a in historial if str(a["fecha"]) >= hace_7_dias
    ]

    # Obtener encuesta de hoy
    encuesta_hoy = encuesta_repository.obtener_encuesta_hoy(usuario_id)
    encuesta_dict = dict(encuesta_hoy) if encuesta_hoy else {"respondida": False}

    gemini_data = gemini_service.analizar_usuario(
        dict(perfil),
        actividades_hoy,
        historial_reciente,
        encuesta_dict
    )

    if gemini_data["exito"]:
        gemini_service.guardar_cache(usuario_id, {
            "recomendaciones": gemini_data["recomendaciones"],
            "resumen": gemini_data["resumen"]
        })

    return {
        "fase": fase_data["fase"],
        "puntos": fase_data["puntos"],
        "color": fase_data["color"],
        "porcentaje": fase_data["porcentaje"],
        "recomendaciones": gemini_data["recomendaciones"] if gemini_data["exito"] else fase_data["recomendaciones"],
        "resumen": gemini_data.get("resumen", ""),
        "ia_activa": gemini_data["exito"],
        "desde_cache": False
    }

# Endpoint para invalidar caché manualmente (se llama al guardar perfil o completar actividad)
@router.post("/gemini/invalidar/{usuario_id}")
def invalidar_cache_gemini(usuario_id: int):
    gemini_service.invalidar_cache(usuario_id)
    return {"mensaje": "Caché invalidado"}
    
@router.post("/encuesta/{usuario_id}")
def guardar_encuesta(usuario_id: int, datos: dict):
    resultado = encuesta_repository.guardar_encuesta(usuario_id, datos)
    # Invalidar caché para que Gemini regenere con los datos de la encuesta
    gemini_service.invalidar_cache(usuario_id)
    return resultado

@router.get("/encuesta/{usuario_id}/hoy")
def obtener_encuesta_hoy(usuario_id: int):
    resultado = encuesta_repository.obtener_encuesta_hoy(usuario_id)
    if not resultado:
        return {"respondida": False}
    return {"respondida": True, **resultado}
    
    
@router.get("/analisis/{usuario_id}")
def obtener_analisis(usuario_id: int):
    perfil = perfil_repository.obtener_perfil_completo(usuario_id)
    if not perfil:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Rango de los últimos 7 días
    hoy = datetime.now().date()
    hace_7 = hoy - timedelta(days=6)
    dias = [(hoy - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]

    # Historial completo
    historial = actividades_repository.obtener_historial_usuario(usuario_id)
    historial = [dict(a) for a in historial]

    # Actividades por día
    actividades_por_dia = []
    for dia in dias:
        acts_dia = [a for a in historial if str(a.get("fecha", "")) == dia]
        completadas = sum(1 for a in acts_dia if a["estado"] == "Completada")
        pendientes  = sum(1 for a in acts_dia if a["estado"] == "Pendiente")
        en_progreso = sum(1 for a in acts_dia if a["estado"] == "En progreso")
        actividades_por_dia.append({
            "fecha": dia,
            "total": len(acts_dia),
            "completadas": completadas,
            "pendientes": pendientes,
            "en_progreso": en_progreso,
            "tasa": round(completadas / len(acts_dia) * 100) if acts_dia else 0
        })

    # Distribución por categoría (últimos 7 días)
    acts_semana = [a for a in historial if str(a.get("fecha","")) >= dias[0]]
    categorias = {}
    for a in acts_semana:
        cat = a.get("categoria", "Personal")
        if cat not in categorias:
            categorias[cat] = {"total": 0, "completadas": 0}
        categorias[cat]["total"] += 1
        if a["estado"] == "Completada":
            categorias[cat]["completadas"] += 1

    # Encuestas de los últimos 7 días
    encuestas_semana = []
    try:
        for dia in dias:
            conn = __import__('backend.database', fromlist=['conectar_base']).conectar_base()
            from psycopg2.extras import RealDictCursor
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT fecha, energia, concentracion, estado_animo, presion_percibida
                FROM encuestas_bienestar
                WHERE usuario_id = %s AND fecha = %s
            """, (usuario_id, dia))
            enc = cur.fetchone()
            cur.close(); conn.close()
            if enc:
                encuestas_semana.append(dict(enc))
            else:
                encuestas_semana.append({"fecha": dia, "energia": None, "concentracion": None, "estado_animo": None, "presion_percibida": None})
    except:
        encuestas_semana = [{"fecha": d, "energia": None, "concentracion": None, "estado_animo": None, "presion_percibida": None} for d in dias]

    # Fase de estrés actual
    todas = actividades_repository.obtener_actividades(usuario_id)
    from backend.services import estres_service
    fase_data = estres_service.calcular_fase_estres(dict(perfil), [dict(a) for a in todas])

    # Estadísticas generales semana
    total_semana      = sum(d["total"] for d in actividades_por_dia)
    completadas_semana = sum(d["completadas"] for d in actividades_por_dia)
    tasa_semana       = round(completadas_semana / total_semana * 100) if total_semana > 0 else 0
    mejor_dia         = max(actividades_por_dia, key=lambda d: d["tasa"]) if total_semana > 0 else None
    peor_dia          = min([d for d in actividades_por_dia if d["total"] > 0], key=lambda d: d["tasa"]) if total_semana > 0 else None

    # Detectar patrones
    patrones = detectar_patrones(actividades_por_dia, historial, dict(perfil), encuestas_semana)

    return {
        "fase": fase_data,
        "dias": dias,
        "actividades_por_dia": actividades_por_dia,
        "categorias": categorias,
        "encuestas_semana": encuestas_semana,
        "stats": {
            "total_semana": total_semana,
            "completadas_semana": completadas_semana,
            "tasa_semana": tasa_semana,
            "mejor_dia": mejor_dia,
            "peor_dia": peor_dia
        },
        "patrones": patrones
    }

def detectar_patrones(actividades_por_dia, historial, perfil, encuestas):
    alertas = []
    insights = []
    nombre = perfil.get("nombre", "").split()[0]

    # Patrón 1: días seguidos sin completar nada
    racha_sin_completar = 0
    for dia in reversed(actividades_por_dia):
        if dia["total"] > 0 and dia["completadas"] == 0:
            racha_sin_completar += 1
        else:
            break

    if racha_sin_completar >= 3:
        alertas.append({
            "tipo": "danger",
            "icono": "🚨",
            "texto": f"Llevas {racha_sin_completar} días seguidos sin completar ninguna actividad. Esto puede indicar sobrecarga o desmotivación. Considera reducir la cantidad de tareas diarias."
        })
    elif racha_sin_completar >= 2:
        alertas.append({
            "tipo": "warning",
            "icono": "⚠️",
            "texto": f"{nombre}, llevas 2 días sin completar actividades. Revisa si tus tareas son realistas para tu tiempo disponible."
        })

    # Patrón 2: mejor categoría
    categorias_completas = {}
    for a in historial:
        cat = a.get("categoria", "Personal")
        if cat not in categorias_completas:
            categorias_completas[cat] = {"total": 0, "completadas": 0}
        categorias_completas[cat]["total"] += 1
        if a["estado"] == "Completada":
            categorias_completas[cat]["completadas"] += 1

    if categorias_completas:
        mejor_cat = max(
            [c for c in categorias_completas if categorias_completas[c]["total"] >= 2],
            key=lambda c: categorias_completas[c]["completadas"] / categorias_completas[c]["total"],
            default=None
        )
        peor_cat = min(
            [c for c in categorias_completas if categorias_completas[c]["total"] >= 2],
            key=lambda c: categorias_completas[c]["completadas"] / categorias_completas[c]["total"],
            default=None
        )
        if mejor_cat:
            tasa_mejor = round(categorias_completas[mejor_cat]["completadas"] / categorias_completas[mejor_cat]["total"] * 100)
            insights.append({
                "icono": "💪",
                "texto": f"Eres más efectivo en actividades de '{mejor_cat}' — completas el {tasa_mejor}% de ellas. Programa las tareas más importantes en esta categoría cuando tengas más energía."
            })
        if peor_cat and peor_cat != mejor_cat:
            tasa_peor = round(categorias_completas[peor_cat]["completadas"] / categorias_completas[peor_cat]["total"] * 100)
            insights.append({
                "icono": "📊",
                "texto": f"Las actividades de '{peor_cat}' son las que menos completas ({tasa_peor}%). Considera dividirlas en tareas más pequeñas o asignarles menor duración estimada."
            })

    # Patrón 3: tendencia de encuestas
    encuestas_con_datos = [e for e in encuestas if e.get("energia") is not None]
    if len(encuestas_con_datos) >= 3:
        energias = [e["energia"] for e in encuestas_con_datos[-3:]]
        if all(energias[i] <= energias[i-1] for i in range(1, len(energias))):
            alertas.append({
                "tipo": "warning",
                "icono": "📉",
                "texto": f"Tu energía ha bajado consistentemente los últimos {len(energias)} días que respondiste la encuesta. Esto es una señal temprana de agotamiento — actúa antes de llegar al límite."
            })
        elif all(energias[i] >= energias[i-1] for i in range(1, len(energias))):
            insights.append({
                "icono": "📈",
                "texto": f"Tu nivel de energía ha mejorado los últimos {len(energias)} días. Mantén los hábitos actuales — algo está funcionando bien."
            })

    # Patrón 4: tasa de completado general
    dias_con_actividades = [d for d in actividades_por_dia if d["total"] > 0]
    if dias_con_actividades:
        tasa_promedio = sum(d["tasa"] for d in dias_con_actividades) / len(dias_con_actividades)
        if tasa_promedio >= 75:
            insights.append({
                "icono": "🏆",
                "texto": f"Tu tasa de completado esta semana es del {round(tasa_promedio)}% — excelente. Eres consistente y realista con tu planificación."
            })
        elif tasa_promedio < 40:
            alertas.append({
                "tipo": "warning",
                "icono": "📋",
                "texto": f"Tu tasa de completado esta semana es solo del {round(tasa_promedio)}%. Estás planeando más de lo que puedes ejecutar. Reduce a máximo {max(2, round(sum(d['total'] for d in dias_con_actividades) / len(dias_con_actividades) * 0.6))} actividades por día."
            })

    return {"alertas": alertas, "insights": insights}
    
@router.post("/mfa/enviar/{usuario_id}")
def enviar_mfa(usuario_id: int, datos: dict):
    tipo = datos.get("tipo", "login")

    perfil = perfil_repository.obtener_perfil_completo(usuario_id)
    if not perfil:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    from backend.services.email_service import generar_codigo, enviar_codigo

    codigo = generar_codigo()
    mfa_repository.guardar_codigo(usuario_id, codigo, tipo)

    # Enviar en background
    def enviar_en_background():
        enviar_codigo(perfil["email"], codigo, tipo)

    hilo = threading.Thread(target=enviar_en_background)
    hilo.daemon = True
    hilo.start()

    return {"mensaje": "Código enviado", "email": perfil["email"]}

@router.post("/mfa/verificar/{usuario_id}")
def verificar_mfa(usuario_id: int, datos: dict):
    codigo = datos.get("codigo")
    tipo   = datos.get("tipo", "login")

    if not codigo:
        raise HTTPException(status_code=400, detail="Código requerido")

    resultado = mfa_repository.verificar_codigo(usuario_id, codigo, tipo)

    if not resultado["valido"]:
        raise HTTPException(status_code=400, detail=resultado["razon"])

    if tipo == "registro":
        mfa_repository.marcar_usuario_verificado(usuario_id)

    return {"mensaje": "Código verificado correctamente"}
