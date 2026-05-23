from backend.database import conectar_base
from psycopg2.extras import RealDictCursor

def crear_actividad(usuario_id: int, datos: dict):
    conexion = conectar_base()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    consulta = """
    INSERT INTO actividades (usuario_id, nombre, descripcion, duracion, prioridad, estado, categoria, fecha)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id, nombre, descripcion, duracion, prioridad, estado, categoria, fecha
    """
    cursor.execute(consulta, (
        usuario_id, datos["nombre"], datos.get("descripcion", ""),
        datos["duracion"], datos.get("prioridad", "Media"),
        datos.get("estado", "Pendiente"), datos.get("categoria", "Personal"), datos["fecha"]
    ))
    actividad = cursor.fetchone()
    conexion.commit()
    cursor.close(); conexion.close()
    return actividad

def obtener_actividades(usuario_id: int):
    conexion = conectar_base()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT id, nombre, descripcion, duracion, prioridad, estado, categoria, fecha
        FROM actividades WHERE usuario_id = %s ORDER BY fecha ASC, prioridad DESC
    """, (usuario_id,))
    actividades = cursor.fetchall()
    cursor.close(); conexion.close()
    return actividades

def eliminar_actividad(actividad_id: int, usuario_id: int):
    conexion = conectar_base()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM actividades WHERE id = %s AND usuario_id = %s", (actividad_id, usuario_id))
    conexion.commit()
    cursor.close(); conexion.close()
    return {"mensaje": "Actividad eliminada"}

def actualizar_estado(actividad_id: int, usuario_id: int, estado: str):
    conexion = conectar_base()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE actividades SET estado = %s WHERE id = %s AND usuario_id = %s",
        (estado, actividad_id, usuario_id)
    )
    conexion.commit()
    cursor.close(); conexion.close()
    return {"mensaje": "Estado actualizado"}

def iniciar_actividad(actividad_id: int, usuario_id: int):
    conexion = conectar_base()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        UPDATE actividades 
        SET estado = 'En progreso', hora_inicio = NOW()
        WHERE id = %s AND usuario_id = %s
        RETURNING id, nombre, duracion, hora_inicio
    """, (actividad_id, usuario_id))
    actividad = cursor.fetchone()
    conexion.commit()
    cursor.close(); conexion.close()
    return actividad

def obtener_actividad_en_curso(usuario_id: int):
    conexion = conectar_base()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT id, nombre, duracion, hora_inicio, categoria
        FROM actividades
        WHERE usuario_id = %s AND estado = 'En progreso' AND hora_inicio IS NOT NULL
        ORDER BY hora_inicio DESC LIMIT 1
    """, (usuario_id,))
    actividad = cursor.fetchone()
    cursor.close(); conexion.close()
    return actividad

def pausar_actividad(actividad_id: int, usuario_id: int):
    conexion = conectar_base()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        INSERT INTO pausas_actividad (actividad_id, hora_pausa)
        VALUES (%s, NOW())
        RETURNING id, hora_pausa
    """, (actividad_id,))
    pausa = cursor.fetchone()
    conexion.commit()
    cursor.close(); conexion.close()
    return pausa

def reanudar_actividad(actividad_id: int, usuario_id: int):
    conexion = conectar_base()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT id, hora_pausa FROM pausas_actividad
        WHERE actividad_id = %s AND hora_reanudacion IS NULL
        ORDER BY hora_pausa DESC LIMIT 1
    """, (actividad_id,))
    pausa = cursor.fetchone()
    if not pausa:
        cursor.close(); conexion.close()
        return None
    cursor.execute("""
        UPDATE pausas_actividad
        SET hora_reanudacion = NOW(),
            duracion_pausa = EXTRACT(EPOCH FROM (NOW() - hora_pausa))::INTEGER
        WHERE id = %s
        RETURNING duracion_pausa
    """, (pausa["id"],))
    resultado = cursor.fetchone()
    cursor.execute("""
        UPDATE actividades
        SET tiempo_pausas = COALESCE(tiempo_pausas, 0) + %s
        WHERE id = %s
    """, (resultado["duracion_pausa"], actividad_id))
    conexion.commit()
    cursor.close(); conexion.close()
    return resultado

def finalizar_actividad(actividad_id: int, usuario_id: int, estado: str, notas: str = None):
    conexion = conectar_base()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT duracion, hora_inicio, tiempo_pausas FROM actividades
        WHERE id = %s AND usuario_id = %s
    """, (actividad_id, usuario_id))
    act = cursor.fetchone()
    if not act:
        cursor.close(); conexion.close()
        return None
    completada_en_tiempo = None
    if act["hora_inicio"]:
        from datetime import datetime, timezone
        ahora = datetime.now(timezone.utc)
        hora_inicio = act["hora_inicio"]
        if hora_inicio.tzinfo is None:
            hora_inicio = hora_inicio.replace(tzinfo=timezone.utc)
        segundos_totales = (ahora - hora_inicio).total_seconds()
        segundos_activos = segundos_totales - (act["tiempo_pausas"] or 0)
        duracion_estimada = act["duracion"] * 60
        completada_en_tiempo = segundos_activos <= duracion_estimada * 1.1
    cursor.execute("""
        UPDATE actividades
        SET estado = %s, hora_fin = NOW(), completada_en_tiempo = %s, notas = %s
        WHERE id = %s AND usuario_id = %s
        RETURNING id, nombre, hora_inicio, hora_fin, duracion, tiempo_pausas, completada_en_tiempo
    """, (estado, completada_en_tiempo, notas, actividad_id, usuario_id))
    resultado = cursor.fetchone()
    conexion.commit()
    cursor.close(); conexion.close()
    return resultado

def obtener_historial_actividad(actividad_id: int, usuario_id: int):
    conexion = conectar_base()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT a.id, a.nombre, a.descripcion, a.categoria, a.prioridad,
               a.estado, a.fecha, a.duracion, a.hora_inicio, a.hora_fin,
               a.tiempo_pausas, a.completada_en_tiempo, a.notas
        FROM actividades a
        WHERE a.id = %s AND a.usuario_id = %s
    """, (actividad_id, usuario_id))
    actividad = cursor.fetchone()
    if not actividad:
        cursor.close(); conexion.close()
        return None
    cursor.execute("""
        SELECT id, hora_pausa, hora_reanudacion, duracion_pausa
        FROM pausas_actividad WHERE actividad_id = %s ORDER BY hora_pausa ASC
    """, (actividad_id,))
    pausas = cursor.fetchall()
    cursor.close(); conexion.close()
    return {"actividad": dict(actividad), "pausas": [dict(p) for p in pausas]}

def obtener_historial_usuario(usuario_id: int):
    conexion = conectar_base()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT a.id, a.nombre, a.categoria, a.prioridad, a.estado,
               a.fecha, a.duracion, a.hora_inicio, a.hora_fin,
               a.tiempo_pausas, a.completada_en_tiempo, a.notas,
               COUNT(p.id) as num_pausas
        FROM actividades a
        LEFT JOIN pausas_actividad p ON a.id = p.actividad_id
        WHERE a.usuario_id = %s
        GROUP BY a.id
        ORDER BY a.fecha DESC, a.hora_inicio DESC NULLS LAST
    """, (usuario_id,))
    actividades = cursor.fetchall()
    cursor.close(); conexion.close()
    return [dict(a) for a in actividades]
