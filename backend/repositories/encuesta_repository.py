from backend.database import conectar_base
from psycopg2.extras import RealDictCursor

def guardar_encuesta(usuario_id: int, datos: dict):
    conexion = conectar_base()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        INSERT INTO encuestas_bienestar 
            (usuario_id, fecha, energia, concentracion, estado_animo, presion_percibida, comentario)
        VALUES (%s, CURRENT_DATE, %s, %s, %s, %s, %s)
        ON CONFLICT (usuario_id, fecha)
        DO UPDATE SET
            energia = %s,
            concentracion = %s,
            estado_animo = %s,
            presion_percibida = %s,
            comentario = %s,
            creado_en = NOW()
        RETURNING *
    """, (
        usuario_id,
        datos["energia"], datos["concentracion"],
        datos["estado_animo"], datos["presion_percibida"],
        datos.get("comentario", ""),
        datos["energia"], datos["concentracion"],
        datos["estado_animo"], datos["presion_percibida"],
        datos.get("comentario", "")
    ))
    resultado = cursor.fetchone()
    conexion.commit()
    cursor.close()
    conexion.close()
    return resultado

def obtener_encuesta_hoy(usuario_id: int):
    conexion = conectar_base()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT * FROM encuestas_bienestar
        WHERE usuario_id = %s AND fecha = CURRENT_DATE
    """, (usuario_id,))
    resultado = cursor.fetchone()
    cursor.close()
    conexion.close()
    return resultado
