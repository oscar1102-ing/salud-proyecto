import psycopg2
from psycopg2.extras import RealDictCursor
import os

def conectar_base():
    database_url = os.environ.get("DATABASE_URL")
    
    if database_url:
        # Railway — usa la URL completa
        conexion = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    else:
        # Local — usa credenciales directas
        conexion = psycopg2.connect(
            host="localhost",
            database="proyecto_salud",
            user="oscar",
            password="1234",
            cursor_factory=RealDictCursor
        )
    return conexion
