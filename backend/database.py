import psycopg2
from psycopg2.extras import RealDictCursor

def conectar_base():
    conexion = psycopg2.connect(
        host ="localhost",
        database = "proyecto_salud",
        user = "oscar",
        password = "1234",
        cursor_factory=RealDictCursor
    )
    return conexion
