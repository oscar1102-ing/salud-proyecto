import psycopg2
from psycopg2.extras import RealDictCursor

def conectar_base():
    conexion = psycopg2.connect(
        host ="localhost",
        database = "proyecto-salud",
        user = "postgres",
        password = "Juli1102-",
        cursor_factory=RealDictCursor
    )
    return conexion