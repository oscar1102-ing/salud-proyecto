from backend.database import conectar_base

def obtener_id_tipo_usuario(tipo: str):
    conexion = conectar_base()
    cursor = conexion.cursor()
    
    cursor.execute("SELECT id FROM tipos_usuario WHERE tipo = %s", (tipo,))
    resultado = cursor.fetchone()
    
    cursor.close()
    conexion.close()
    
    return resultado['id'] if resultado else None

def obtener_id_nivel_carga(nivel: str):
    conexion = conectar_base()
    cursor = conexion.cursor()
    
    cursor.execute("SELECT id FROM niveles_carga WHERE nivel = %s", (nivel,))
    resultado = cursor.fetchone()
    
    cursor.close()
    conexion.close()
    
    return resultado['id'] if resultado else None