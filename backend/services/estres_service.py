def calcular_fase_estres(perfil: dict, actividades: list) -> dict:
    puntos = 0

    # --- Horas trabajo vs descanso ---
    horas_trabajo  = perfil.get("horas_trabajo", 0)
    horas_descanso = perfil.get("horas_descanso", 0)

    if horas_trabajo >= 10:
        puntos += 3
    elif horas_trabajo >= 7:
        puntos += 2
    elif horas_trabajo >= 4:
        puntos += 1

    if horas_descanso <= 4:
        puntos += 3
    elif horas_descanso <= 6:
        puntos += 2
    elif horas_descanso <= 7:
        puntos += 1

    # --- Nivel de carga declarado ---
    nivel = perfil.get("nivel_carga", "Medio")
    if nivel == "Alto":
        puntos += 3
    elif nivel == "Medio":
        puntos += 1

    # --- Actividades pendientes de alta prioridad ---
    pendientes_alta = [
        a for a in actividades
        if a["prioridad"] == "Alta" and a["estado"] != "Completada"
    ]
    puntos += min(len(pendientes_alta), 4)  # máximo 4 puntos por esto

    # --- Total actividades sin completar ---
    sin_completar = [a for a in actividades if a["estado"] != "Completada"]
    if len(sin_completar) >= 8:
        puntos += 2
    elif len(sin_completar) >= 4:
        puntos += 1

    # --- Determinar fase ---
    if puntos <= 4:
        fase = "Alarma"
        color = "#22c55e"       # verde
        porcentaje = 25
    elif puntos <= 8:
        fase = "Resistencia"
        color = "#eab308"       # amarillo
        porcentaje = 60
    else:
        fase = "Agotamiento"
        color = "#ef4444"       # rojo
        porcentaje = 90

    # --- Recomendaciones ---
    recomendaciones = generar_recomendaciones(perfil, actividades, fase)

    return {
        "fase": fase,
        "puntos": puntos,
        "color": color,
        "porcentaje": porcentaje,
        "recomendaciones": recomendaciones
    }


def generar_recomendaciones(perfil: dict, actividades: list, fase: str) -> list:
    recs = []

    horas_trabajo  = perfil.get("horas_trabajo", 0)
    horas_descanso = perfil.get("horas_descanso", 0)
    nivel          = perfil.get("nivel_carga", "Medio")

    # Recomendaciones por horas
    if horas_trabajo > horas_descanso * 2:
        recs.append({
            "icono": "😴",
            "texto": f"Trabajas {horas_trabajo}h pero solo descansas {horas_descanso}h. Intenta aumentar tu descanso a al menos {round(horas_trabajo * 0.6)}h."
        })

    if horas_descanso < 6:
        recs.append({
            "icono": "🛌",
            "texto": "Menos de 6 horas de descanso afecta tu concentración y memoria. Prioriza el sueño."
        })

    # Recomendaciones por actividades
    pendientes_alta = [
        a for a in actividades
        if a["prioridad"] == "Alta" and a["estado"] != "Completada"
    ]
    if len(pendientes_alta) >= 3:
        recs.append({
            "icono": "⚠️",
            "texto": f"Tienes {len(pendientes_alta)} tareas de alta prioridad sin completar. Considera delegar o redistribuir."
        })

    sin_completar = [a for a in actividades if a["estado"] != "Completada"]
    if len(sin_completar) >= 6:
        recs.append({
            "icono": "📋",
            "texto": f"Tienes {len(sin_completar)} actividades pendientes. Divide las tareas grandes en pasos más pequeños."
        })

    # Recomendaciones por fase
    if fase == "Agotamiento":
        recs.append({
            "icono": "🧘",
            "texto": "Estás en zona de agotamiento. Toma pausas de 10 minutos cada hora y evita agregar nuevas tareas hoy."
        })
        recs.append({
            "icono": "🚶",
            "texto": "Una caminata corta de 15-20 minutos puede reducir el cortisol significativamente."
        })
    elif fase == "Resistencia":
        recs.append({
            "icono": "⏱️",
            "texto": "Usa la técnica Pomodoro: 25 minutos de trabajo, 5 de descanso."
        })
    else:
        recs.append({
            "icono": "✅",
            "texto": "Tu carga está equilibrada. Mantén tus hábitos actuales."
        })

    return recs
