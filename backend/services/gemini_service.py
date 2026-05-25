import os
import json
from google import genai
from datetime import datetime, timedelta
from backend.database import conectar_base
from psycopg2.extras import RealDictCursor

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)

# ==================== CACHÉ ====================

def obtener_cache(usuario_id: int) -> dict:
    """Devuelve la respuesta cacheada de hoy si existe y es válida."""
    try:
        conexion = conectar_base()
        cursor = conexion.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT respuesta FROM gemini_cache
            WHERE usuario_id = %s AND fecha = CURRENT_DATE AND invalido = FALSE
        """, (usuario_id,))
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        if resultado:
            return resultado["respuesta"]
        return None
    except Exception as e:
        print(f"Error leyendo caché: {e}")
        return None

def guardar_cache(usuario_id: int, respuesta: dict):
    """Guarda o actualiza la respuesta de Gemini para hoy."""
    try:
        conexion = conectar_base()
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO gemini_cache (usuario_id, fecha, respuesta, invalido, actualizado_en)
            VALUES (%s, CURRENT_DATE, %s, FALSE, NOW())
            ON CONFLICT (usuario_id, fecha)
            DO UPDATE SET respuesta = %s, invalido = FALSE, actualizado_en = NOW()
        """, (usuario_id, json.dumps(respuesta), json.dumps(respuesta)))
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as e:
        print(f"Error guardando caché: {e}")

def invalidar_cache(usuario_id: int):
    """Marca el caché como inválido para forzar nueva consulta a Gemini."""
    try:
        conexion = conectar_base()
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE gemini_cache SET invalido = TRUE
            WHERE usuario_id = %s AND fecha = CURRENT_DATE
        """, (usuario_id,))
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as e:
        print(f"Error invalidando caché: {e}")

# ==================== GEMINI ====================


def analizar_usuario(perfil: dict, actividades_hoy: list, historial_reciente: list, encuesta_hoy: dict = None) -> dict:
    try:
        if actividades_hoy:
            resumen_hoy = "\n".join([
                f"- {a['nombre']} ({a['categoria']}, {a['duracion']} min, prioridad {a['prioridad']}, estado: {a['estado']})"
                for a in actividades_hoy
            ])
        else:
            resumen_hoy = "No tiene actividades programadas para hoy."

        if historial_reciente:
            total        = len(historial_reciente)
            completadas  = sum(1 for a in historial_reciente if a["estado"] == "Completada")
            fuera_tiempo = sum(1 for a in historial_reciente if a.get("completada_en_tiempo") == False)
            total_pausas = sum(int(a.get("num_pausas") or 0) for a in historial_reciente)

            categorias = {}
            for a in historial_reciente:
                cat = a.get("categoria", "Sin categoría")
                if cat not in categorias:
                    categorias[cat] = {"total": 0, "completadas": 0}
                categorias[cat]["total"] += 1
                if a["estado"] == "Completada":
                    categorias[cat]["completadas"] += 1

            patron_categorias = ", ".join([
                f"{cat}: {v['completadas']}/{v['total']} completadas"
                for cat, v in categorias.items()
            ])
            resumen_historial = (
                f"En los últimos 7 días completó {completadas} de {total} actividades. "
                f"{fuera_tiempo} actividades fueron completadas fuera del tiempo estimado. "
                f"Total de pausas registradas: {total_pausas}. "
                f"Rendimiento por categoría: {patron_categorias}."
            )
        else:
            resumen_historial = "No tiene historial de actividades reciente."

        # ← AQUÍ, ANTES DEL PROMPT
        if encuesta_hoy and encuesta_hoy.get("respondida"):
            emojis = {1: "😩 Muy mal", 2: "😟 Mal", 3: "😐 Regular", 4: "🙂 Bien", 5: "😄 Muy bien"}
            resumen_encuesta = (
                f"El usuario reportó hoy: "
                f"Energía {emojis.get(encuesta_hoy.get('energia'), '—')}, "
                f"Concentración {emojis.get(encuesta_hoy.get('concentracion'), '—')}, "
                f"Estado de ánimo {emojis.get(encuesta_hoy.get('estado_animo'), '—')}, "
                f"Presión percibida {emojis.get(encuesta_hoy.get('presion_percibida'), '—')}."
            )
            if encuesta_hoy.get("comentario"):
                resumen_encuesta += f" Comentario: \"{encuesta_hoy['comentario']}\"."
        else:
            resumen_encuesta = "El usuario no ha respondido la encuesta de hoy."

        prompt = f"""Eres un asistente experto en bienestar, productividad y manejo del estrés.
Analiza el perfil completo de este usuario y genera recomendaciones MUY personalizadas, específicas y accionables.
NO des consejos genéricos. Basa cada recomendación en los datos reales del usuario.

PERFIL DEL USUARIO:
- Nombre: {perfil.get('nombre', 'Usuario')}
- Tipo: {perfil.get('tipo_usuario', 'No especificado')}
- Edad: {perfil.get('edad', 'No especificada')} años
- Horas de trabajo diarias: {perfil.get('horas_trabajo', 0)}h
- Horas de descanso diarias: {perfil.get('horas_descanso', 0)}h
- Nivel de carga declarado: {perfil.get('nivel_carga', 'Medio')}

ACTIVIDADES DE HOY:
{resumen_hoy}

HISTORIAL ÚLTIMOS 7 DÍAS:
{resumen_historial}

ESTADO SUBJETIVO DEL USUARIO HOY:
{resumen_encuesta}

INSTRUCCIONES:
1. Genera exactamente 4 recomendaciones personalizadas basadas en los datos reales
2. Cada recomendación debe mencionar datos específicos del usuario
3. Sé directo y concreto, no uses frases vacías
4. Incluye una recomendación sobre su patrón de pausas si es relevante
5. Responde ÚNICAMENTE en este formato JSON, sin texto adicional, sin markdown:

{{
  "recomendaciones": [
    {{"icono": "emoji", "texto": "recomendación específica aquí"}},
    {{"icono": "emoji", "texto": "recomendación específica aquí"}},
    {{"icono": "emoji", "texto": "recomendación específica aquí"}},
    {{"icono": "emoji", "texto": "recomendación específica aquí"}}
  ],
  "resumen": "Una frase corta y honesta sobre el estado actual del usuario"
}}"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        texto = response.text.strip()
        if "```" in texto:
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
        texto = texto.strip()

        resultado = json.loads(texto)
        return {
            "exito": True,
            "recomendaciones": resultado.get("recomendaciones", []),
            "resumen": resultado.get("resumen", "")
        }

    except Exception as e:
        print(f"Error en Gemini: {e}")
        return {
            "exito": False,
            "recomendaciones": [],
            "resumen": ""
        }
