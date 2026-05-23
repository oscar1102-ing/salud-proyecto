from backend.repositories import usuario_repository as repo
from backend.repositories import perfil_repository as perfil_repo
from backend.repositories import catalogos_repository as catalogos_repo
from fastapi import HTTPException

import bcrypt

def registrar_usuario(datos):
    
    # 1. Verificar si el email ya existe
    if repo.verificar_email_existe(datos.email):
        return {"error": "El correo ya está registrado"}
    
    # 2. Validar que el tipo de usuario exista
    tipo_id = catalogos_repo.obtener_id_tipo_usuario(datos.tipo_usuario)
    if not tipo_id:
        return {"error": f"Tipo de usuario '{datos.tipo_usuario}' no válido"}
    
    # 3. Validar que el nivel de carga exista
    nivel_id = catalogos_repo.obtener_id_nivel_carga(datos.nivel_carga)
    if not nivel_id:
        return {"error": f"Nivel de carga '{datos.nivel_carga}' no válido"}
    
    # 4. Validar que las horas sean positivas
    if datos.horas_trabajo < 0 or datos.horas_descanso < 0:
        return {"error": "Las horas no pueden ser negativas"}
    
    # 5. Crear el usuario
    usuario = repo.crear_usuario(
        datos.nombre_completo,
        datos.email,
        datos.password,
        datos.edad
    )
    
    if not usuario:
        return {"error": "Error al crear usuario"}
    
    # 6. Crear el perfil del usuario
    perfil_repo.crear_perfil(
        usuario['id'],
        tipo_id,
        nivel_id,
        datos.horas_trabajo,
        datos.horas_descanso
    )
    
    # 7. Obtener perfil completo para respuesta
    perfil_completo = perfil_repo.obtener_perfil_completo(usuario['id'])
    
    return {
        "mensaje": "Registro exitoso",
        "usuario": perfil_completo
    }



def login_usuario(data):
    usuario = repo.buscar_por_email(data.email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not bcrypt.checkpw(data.password.encode('utf-8'), usuario["password"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    # Devuelve id y nombre para guardarlo en el frontend
    return {
        "mensaje": "Login exitoso",
        "usuario_id": usuario["id"],
        "nombre": usuario["nombre"]
    }
