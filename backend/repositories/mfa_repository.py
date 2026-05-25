from backend.database import conectar_base
from datetime import datetime, timezone, timedelta

def guardar_codigo(usuario_id: int, codigo: str, tipo: str):
    conexion = conectar_base()
    cursor = conexion.cursor()

    # Invalidar códigos anteriores del mismo tipo
    cursor.execute("""
        UPDATE codigos_mfa SET usado = TRUE
        WHERE usuario_id = %s AND tipo = %s AND usado = FALSE
    """, (usuario_id, tipo))

    # Guardar nuevo código con expiración de 10 minutos
    expira = datetime.now(timezone.utc) + timedelta(minutes=10)
    cursor.execute("""
        INSERT INTO codigos_mfa (usuario_id, codigo, tipo, expira_en)
        VALUES (%s, %s, %s, %s)
    """, (usuario_id, codigo, tipo, expira))

    conexion.commit()
    cursor.close()
    conexion.close()

def verificar_codigo(usuario_id: int, codigo: str, tipo: str):
    conexion = conectar_base()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, expira_en FROM codigos_mfa
        WHERE usuario_id = %s AND codigo = %s AND tipo = %s AND usado = FALSE
        ORDER BY creado_en DESC LIMIT 1
    """, (usuario_id, codigo, tipo))

    registro = cursor.fetchone()

    if not registro:
        cursor.close()
        conexion.close()
        return {"valido": False, "razon": "Código incorrecto"}

    expira = registro["expira_en"]
    if expira.tzinfo is None:
        expira = expira.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expira:
        cursor.close()
        conexion.close()
        return {"valido": False, "razon": "Código expirado"}

    # Marcar como usado
    cursor.execute("UPDATE codigos_mfa SET usado = TRUE WHERE id = %s", (registro["id"],))

    conexion.commit()
    cursor.close()
    conexion.close()
    return {"valido": True}

def marcar_usuario_verificado(usuario_id: int):
    conexion = conectar_base()
    cursor = conexion.cursor()
    cursor.execute("UPDATE usuarios SET verificado = TRUE WHERE id = %s", (usuario_id,))
    conexion.commit()
    cursor.close()
    conexion.close()
