from backend.database import conectar_base
import bcrypt

def crear_usuario(nombre: str, email: str, password: str, edad: int):
    conexion = conectar_base()
    cursor = conexion.cursor()
    
    # Hash de la contraseña
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    consulta = """
    INSERT INTO usuarios (nombre, email, password, edad)
    VALUES (%s, %s, %s, %s)
    RETURNING id, nombre, email, edad, fecha_registro
    """
    
    cursor.execute(consulta, (nombre, email, hashed.decode('utf-8'), edad))
    usuario = cursor.fetchone()
    
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return usuario

def obtener_usuario_por_email(email: str):
    conexion = conectar_base()
    cursor = conexion.cursor()
    
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    usuario = cursor.fetchone()
    
    cursor.close()
    conexion.close()
    
    return usuario

def verificar_email_existe(email: str):
    conexion = conectar_base()
    cursor = conexion.cursor()
    
    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
    existe = cursor.fetchone()
    
    cursor.close()
    conexion.close()
    
    return existe is not None


def buscar_por_email(email):
    conn = conectar_base()
    cursor = conn.cursor()
    query = "SELECT id, nombre, email, password, verificado FROM usuarios WHERE email = %s"
    cursor.execute(query, (email,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return result
    return None
