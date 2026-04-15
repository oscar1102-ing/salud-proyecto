from backend.database import conectar_base

def crear_perfil(usuario_id: int, tipo_usuario_id: int, nivel_carga_id: int, 
                 horas_trabajo: int, horas_descanso: int):
    conexion = conectar_base()
    cursor = conexion.cursor()
    
    consulta = """
    INSERT INTO perfil_usuario (usuario_id, tipo_usuario_id, nivel_carga_id, 
                                horas_trabajo, horas_descanso)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id
    """
    
    cursor.execute(consulta, (usuario_id, tipo_usuario_id, nivel_carga_id,
                             horas_trabajo, horas_descanso))
    perfil_id = cursor.fetchone()
    
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return perfil_id

def obtener_perfil_completo(usuario_id: int):
    conexion = conectar_base()
    cursor = conexion.cursor()
    
    consulta = """
    SELECT u.id, u.nombre, u.email, u.edad, u.fecha_registro,
           tu.tipo as tipo_usuario,
           nc.nivel as nivel_carga,
           pu.horas_trabajo, pu.horas_descanso
    FROM usuarios u
    JOIN perfil_usuario pu ON u.id = pu.usuario_id
    JOIN tipos_usuario tu ON pu.tipo_usuario_id = tu.id
    JOIN niveles_carga nc ON pu.nivel_carga_id = nc.id
    WHERE u.id = %s
    """
    
    cursor.execute(consulta, (usuario_id,))
    perfil = cursor.fetchone()
    
    cursor.close()
    conexion.close()
    
    return perfil