import google.generativeai as genai
import os
from datetime import datetime, timedelta

# Configura tu API key aquí o mejor en variable de entorno
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)

def analizar_usuario(perfil: dict, actividades_hoy: list, historial_reciente: list) -> dict:
    """
    Le manda a Gemini el contexto completo del usuario y obtiene
    recomendaciones personalizadas e inteligentes.
    """
    try:
        # Armar contexto de actividades de hoy
        if actividades_hoy:
            resumen_hoy = "\n".join([
                f"- {a['nombre']} ({a['categoria']}, {a['duracion']} min, prioridad {a['prioridad']}, estado: {a['estado']})"
                for a in actividades_hoy
            ])
        else:
            resumen_hoy = "No tiene actividades programadas para hoy."

        # Armar contexto del historial reciente (últimos 7 días)
        if historial_reciente:
            total = len(historial_reciente)
            completadas = sum(1 for a in historial_reciente if a["estado"] == "Completada")
            fuera_tiempo = sum(1 for a in historial_reciente if a.get("completada_en_tiempo") == False)
            total_pausas = sum(int(a.get("num_pausas") or 0) for a in historial_reciente)
            
            resumen_historial = (
                f"En los últimos 7 días completó {completadas} de {total} actividades. "
                f"{fuera_tiempo} actividades fueron completadas fuera del tiempo estimado. "
                f"Total de pausas registradas: {total_pausas}."
            )
            
            # Patrones por categoría
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
            resumen_historial += f" Rendimiento por categoría: {patron_categorias}."
        else:
            resumen_historial = "No tiene historial de actividades reciente."

        # Prompt para Gemini
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

INSTRUCCIONES:
1. Genera exactamente 4 recomendaciones personalizadas basadas en los datos reales
2. Cada recomendación debe mencionar datos específicos del usuario (sus horas, sus categorías, sus patrones)
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
  "resumen": "Una frase corta y honesta sobre el estado actual del usuario basada en sus datos"
}}"""

        model = genai.GenerativeModel("gemini-1.5-flash")
        respuesta = model.generate_content(prompt)
        
        # Limpiar y parsear JSON
        import json
        texto = respuesta.text.strip()
        # Quitar posibles bloques de código markdown
        if texto.startswith("```"):
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
