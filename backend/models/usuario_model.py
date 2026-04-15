from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UsuarioRegistro(BaseModel):
    nombre_completo: str
    email: EmailStr
    password: str
    edad: Optional[int] = None
    tipo_usuario: str  # 'Estudiante' o 'Trabajador'
    nivel_carga: str   # 'Bajo', 'Medio' o 'Alto'
    horas_trabajo: int
    horas_descanso: int

class UsuarioRespuesta(BaseModel):
    id: int
    nombre: str
    email: str
    edad: Optional[int]
    fecha_registro: datetime
    tipo_usuario: str
    nivel_carga: str
    horas_trabajo: int
    horas_descanso: int

class LoginData(BaseModel):
    email: str
    password: str