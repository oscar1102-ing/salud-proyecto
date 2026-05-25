from datetime import datetime, timedelta

def calcular_fase_estres(perfil: dict, actividades: list) -> dict:
    puntos = 0
    factores = []  # para rastrear qué está afectando el estrés

    horas_trabajo  = perfil.get("horas_trabajo", 0)
    horas_descanso = perfil.get("horas_descanso", 0)
    nivel_carga    = perfil.get("nivel_carga", "Medio")
    tipo_usuario   = perfil.get("tipo_usuario", "Estudiante")
    hoy            = datetime.now().strftime("%Y-%m-%d")
    hora_actual    = datetime.now().hour

    # ==================== FACTOR 1: HORAS DE TRABAJO ====================
    if horas_trabajo >= 12:
        puntos += 5
        factores.append("trabajo_extremo")
    elif horas_trabajo >= 10:
        puntos += 4
        factores.append("trabajo_alto")
    elif horas_trabajo >= 8:
        puntos += 3
        factores.append("trabajo_moderado")
    elif horas_trabajo >= 6:
        puntos += 2
        factores.append("trabajo_normal")
    elif horas_trabajo >= 4:
        puntos += 1

    # ==================== FACTOR 2: HORAS DE DESCANSO ====================
    if horas_descanso <= 3:
        puntos += 5
        factores.append("descanso_critico")
    elif horas_descanso <= 5:
        puntos += 4
        factores.append("descanso_bajo")
    elif horas_descanso <= 6:
        puntos += 2
        factores.append("descanso_insuficiente")
    elif horas_descanso <= 7:
        puntos += 1
    # 8+ horas = 0 puntos (óptimo)

    # ==================== FACTOR 3: RATIO TRABAJO/DESCANSO ====================
    if horas_descanso > 0:
        ratio = horas_trabajo / horas_descanso
        if ratio >= 4:
            puntos += 4
            factores.append("ratio_critico")
        elif ratio >= 3:
            puntos += 3
            factores.append("ratio_alto")
        elif ratio >= 2:
            puntos += 2
            factores.append("ratio_moderado")
        elif ratio >= 1.5:
            puntos += 1
    else:
        puntos += 3  # sin descanso registrado

    # ==================== FACTOR 4: NIVEL DE CARGA DECLARADO ====================
    if nivel_carga == "Alto":
        puntos += 4
        factores.append("carga_alta")
    elif nivel_carga == "Medio":
        puntos += 2
    else:
        puntos += 0

    # ==================== FACTOR 5: ACTIVIDADES HOY ====================
    actividades_hoy = [a for a in actividades if str(a.get("fecha", "")) == hoy]
    pendientes_hoy  = [a for a in actividades_hoy if a["estado"] == "Pendiente"]
    completadas_hoy = [a for a in actividades_hoy if a["estado"] == "Completada"]
    alta_hoy        = [a for a in pendientes_hoy if a["prioridad"] == "Alta"]
    en_progreso_hoy = [a for a in actividades_hoy if a["estado"] == "En progreso"]

    # Penalizar por alta prioridad pendiente
    if len(alta_hoy) >= 4:
        puntos += 4
        factores.append("muchas_altas_hoy")
    elif len(alta_hoy) >= 2:
        puntos += 2
        factores.append("altas_pendientes_hoy")
    elif len(alta_hoy) == 1:
        puntos += 1

    # Bonificar por completadas hoy
    if len(actividades_hoy) > 0:
        tasa_completado = len(completadas_hoy) / len(actividades_hoy)
        if tasa_completado >= 0.8:
            puntos -= 2  # muy productivo hoy
            factores.append("muy_productivo_hoy")
        elif tasa_completado >= 0.5:
            puntos -= 1  # productivo
        elif tasa_completado == 0 and len(actividades_hoy) >= 3:
            puntos += 2  # nada completado con muchas tareas
            factores.append("nada_completado_hoy")

    # ==================== FACTOR 6: ACTIVIDADES VENCIDAS ====================
    ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    hace_7 = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    vencidas_recientes = [
        a for a in actividades
        if str(a.get("fecha", "")) >= hace_7
        and str(a.get("fecha", "")) < hoy
        and a["estado"] == "Pendiente"
    ]
    vencidas_alta = [a for a in vencidas_recientes if a["prioridad"] == "Alta"]

    if len(vencidas_recientes) >= 6:
        puntos += 5
        factores.append("muchas_vencidas")
    elif len(vencidas_recientes) >= 3:
        puntos += 3
        factores.append("vencidas_moderadas")
    elif len(vencidas_recientes) >= 1:
        puntos += 1
        factores.append("pocas_vencidas")

    if len(vencidas_alta) >= 2:
        puntos += 2
        factores.append("vencidas_alta_prioridad")

    # ==================== FACTOR 7: CARGA TOTAL PENDIENTE ====================
    total_pendientes = [a for a in actividades if a["estado"] == "Pendiente"]
    mins_pendientes  = sum(a.get("duracion", 0) for a in total_pendientes)

    if mins_pendientes >= 480:  # 8+ horas pendientes
        puntos += 3
        factores.append("carga_pendiente_critica")
    elif mins_pendientes >= 240:  # 4+ horas
        puntos += 2
        factores.append("carga_pendiente_alta")
    elif mins_pendientes >= 120:  # 2+ horas
        puntos += 1

    # ==================== FACTOR 8: HORA DEL DÍA ====================
    # Penalizar si es tarde y aún hay muchas tareas pendientes
    if hora_actual >= 20 and len(alta_hoy) >= 2:
        puntos += 2
        factores.append("tarde_con_pendientes")
    elif hora_actual >= 22 and len(pendientes_hoy) > 0:
        puntos += 1

    # ==================== NORMALIZAR PUNTOS ====================
    puntos = max(0, puntos)  # no puede ser negativo

    # ==================== DETERMINAR FASE ====================
    # Escala: 0-8 Alarma, 9-16 Resistencia, 17+ Agotamiento
    if puntos <= 8:
        fase       = "Alarma"
        color      = "#22c55e"
        porcentaje = min(95, max(5, int((puntos / 8) * 33)))
    elif puntos <= 16:
        fase       = "Resistencia"
        color      = "#eab308"
        porcentaje = min(95, max(35, int(33 + ((puntos - 8) / 8) * 34)))
    else:
        fase       = "Agotamiento"
        color      = "#ef4444"
        porcentaje = min(98, max(68, int(67 + ((puntos - 16) / 10) * 31)))

    recomendaciones = generar_recomendaciones(
        perfil, actividades, fase, factores,
        actividades_hoy, pendientes_hoy, completadas_hoy,
        alta_hoy, vencidas_recientes, vencidas_alta,
        mins_pendientes
    )

    return {
        "fase": fase,
        "puntos": puntos,
        "color": color,
        "porcentaje": porcentaje,
        "recomendaciones": recomendaciones
    }


def generar_recomendaciones(perfil, actividades, fase, factores,
                             actividades_hoy, pendientes_hoy, completadas_hoy,
                             alta_hoy, vencidas_recientes, vencidas_alta,
                             mins_pendientes) -> list:
    recs = []
    horas_trabajo  = perfil.get("horas_trabajo", 0)
    horas_descanso = perfil.get("horas_descanso", 0)
    nivel_carga    = perfil.get("nivel_carga", "Medio")
    nombre         = perfil.get("nombre", "").split()[0]
    tipo           = perfil.get("tipo_usuario", "Estudiante")
    hora_actual    = datetime.now().hour

    # ── RECOMENDACIÓN 1: Ratio trabajo/descanso ──
    if "ratio_critico" in factores or "descanso_critico" in factores:
        deficit = max(1, round(horas_trabajo * 0.5) - horas_descanso)
        recs.append({
            "icono": "🚨",
            "texto": f"{nombre}, tu ratio trabajo/descanso es crítico: {horas_trabajo}h trabajando vs {horas_descanso}h descansando. "
                     f"Necesitas al menos {deficit}h más de descanso hoy. El agotamiento crónico reduce el rendimiento hasta un 40% — "
                     f"descansar no es perder tiempo, es recuperar capacidad."
        })
    elif "ratio_alto" in factores or "descanso_bajo" in factores:
        recs.append({
            "icono": "😴",
            "texto": f"Con {horas_trabajo}h de trabajo y solo {horas_descanso}h de descanso, tu cerebro opera por debajo de su capacidad. "
                     f"Como {tipo.lower()}, intenta agregar una siesta de 20 minutos o una pausa sin pantallas de 30 minutos — "
                     f"esto puede recuperar hasta el 20% de tu productividad."
        })
    elif "descanso_insuficiente" in factores:
        recs.append({
            "icono": "😴",
            "texto": f"{horas_descanso}h de descanso está por debajo del mínimo recomendado de 7h. "
                     f"Esta noche prioriza dormir a las {max(21, 23 - horas_descanso)}:00 para recuperar el déficit acumulado."
        })

    # ── RECOMENDACIÓN 2: Actividades vencidas ──
    if "muchas_vencidas" in factores or "vencidas_alta_prioridad" in factores:
        nombres = ", ".join([f"'{a['nombre']}'" for a in vencidas_recientes[:2]])
        recs.append({
            "icono": "⚠️",
            "texto": f"Tienes {len(vencidas_recientes)} actividades vencidas esta semana"
                     f"{f', incluyendo {len(vencidas_alta)} de alta prioridad' if vencidas_alta else ''}: {nombres}... "
                     f"Esta acumulación genera estrés invisible. Dedica los próximos 15 minutos a clasificarlas: "
                     f"¿cuáles eliminas, cuáles delegas y cuáles reagendas para esta semana?"
        })
    elif "vencidas_moderadas" in factores:
        recs.append({
            "icono": "📌",
            "texto": f"Tienes {len(vencidas_recientes)} actividades vencidas sin resolver. "
                     f"Cada tarea pendiente consume energía mental aunque no la estés haciendo. "
                     f"Elige la más rápida y complétala ahora — el momentum que genera vale más que su duración."
        })

    # ── RECOMENDACIÓN 3: Carga del día de hoy ──
    if "muchas_altas_hoy" in factores:
        duracion_total = sum(a.get("duracion", 30) for a in alta_hoy)
        recs.append({
            "icono": "🎯",
            "texto": f"Tienes {len(alta_hoy)} tareas de alta prioridad hoy ({duracion_total} minutos en total). "
                     f"Es demasiado para un solo día de calidad. Elige las 2 más críticas para hoy y "
                     f"reagenda las demás — completar 2 bien es mejor que intentar {len(alta_hoy)} a medias."
        })
    elif "altas_pendientes_hoy" in factores and len(alta_hoy) > 0:
        proxima = alta_hoy[0]
        recs.append({
            "icono": "🎯",
            "texto": f"Tu tarea más urgente ahora es '{proxima['nombre']}' ({proxima.get('duracion', 30)} min). "
                     f"Empiézala en los próximos 10 minutos sin revisar mensajes ni redes — "
                     f"el primer bloque del día es cuando tienes mayor capacidad cognitiva."
        })

    # ── RECOMENDACIÓN 4: Carga pendiente total ──
    if "carga_pendiente_critica" in factores:
        horas_pend = round(mins_pendientes / 60, 1)
        dias_necesarios = round(mins_pendientes / (horas_trabajo * 60), 1) if horas_trabajo > 0 else "varios"
        recs.append({
            "icono": "📋",
            "texto": f"Tienes {horas_pend}h de trabajo pendiente acumulado — aproximadamente {dias_necesarios} días de tu ritmo actual. "
                     f"Esto es insostenible. Esta semana aplica la regla del 80/20: identifica las 3 actividades "
                     f"que generan más valor y priorízalas sobre todo lo demás."
        })
    elif "carga_pendiente_alta" in factores:
        horas_pend = round(mins_pendientes / 60, 1)
        recs.append({
            "icono": "📋",
            "texto": f"Tienes {horas_pend}h de trabajo pendiente. Distribuye esta carga en bloques de máximo "
                     f"{'90' if nivel_carga == 'Alto' else '60'} minutos con pausas de 15 entre ellos — "
                     f"trabajar en bloques cortos reduce el agotamiento mental hasta un 25%."
        })

    # ── RECOMENDACIÓN 5: Hora del día + pendientes ──
    if "tarde_con_pendientes" in factores:
        recs.append({
            "icono": "🌙",
            "texto": f"Son las {hora_actual}:00 y aún tienes {len(alta_hoy)} tareas urgentes pendientes. "
                     f"A esta hora tu corteza prefrontal trabaja al 60% de su capacidad. "
                     f"Completa solo la tarea más crítica y deja el resto para mañana a primera hora — "
                     f"forzar trabajo nocturno acumula deuda de sueño que afecta toda la semana."
        })

    # ── RECOMENDACIÓN 6: Productividad positiva ──
    if "muy_productivo_hoy" in factores and len(completadas_hoy) > 0:
        recs.append({
            "icono": "🏆",
            "texto": f"Excelente día, {nombre} — completaste {len(completadas_hoy)} de {len(actividades_hoy)} actividades. "
                     f"Aprovecha este momentum: dedica los próximos 10 minutos a planificar las prioridades de mañana "
                     f"mientras tu mente está en modo productivo."
        })

    # ── RECOMENDACIÓN POR FASE (siempre incluir una) ──
    if fase == "Agotamiento" and len(recs) < 4:
        recs.append({
            "icono": "🧘",
            "texto": f"Estás en zona de agotamiento. Aplica la regla 90/20 ahora: "
                     f"trabaja máximo 90 minutos seguidos, luego 20 minutos de descanso activo — "
                     f"camina, estira, respira. No revisar mensajes durante el descanso. "
                     f"Repite máximo 3 veces por día y para cuando llegues a {min(22, hora_actual + 4)}:00."
        })
    elif fase == "Resistencia" and len(recs) < 4:
        bloques_pomodoro = max(1, round(mins_pendientes / 25)) if mins_pendientes > 0 else len(pendientes_hoy) * 2
        recs.append({
            "icono": "⏱️",
            "texto": f"Tu nivel es moderado y controlable. Usa Pomodoro: 25 minutos de trabajo enfocado, "
                     f"5 de pausa. Para tu carga actual necesitas aproximadamente {bloques_pomodoro} bloques. "
                     f"Empieza por la tarea más difícil — tu energía ahora es mayor que en la tarde."
        })
    elif fase == "Alarma" and len(recs) < 4:
        recs.append({
            "icono": "✅",
            "texto": f"Tu nivel de estrés está bajo control, {nombre}. "
                     f"Es el momento ideal para avanzar en actividades importantes pero no urgentes — "
                     f"las que generan valor a largo plazo. Mantén el hábito de planificar el día siguiente "
                     f"antes de dormir: reduce la ansiedad matutina hasta un 30%."
        })

    # Retornar máximo 4, priorizando las más relevantes
    return recs[:4]
