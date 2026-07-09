from pydantic import BaseModel, Field
from typing import Optional

# ==========================================
# 1. SCHEMAS PARA AUTENTICACIÓN Y REGISTRO
# ==========================================

class UsuarioCreate(BaseModel):
    """
    DTO para la creación/registro de nuevos usuarios en el sistema.
    Recibe la contraseña en texto plano para ser encriptada en la capa de servicio.
    """
    username: str = Field(..., min_length=3, max_length=50, examples=["vendedor_juan"])
    password: str = Field(..., min_length=6, description="Contraseña en texto plano a encriptar", examples=["ClaveSegura123"])
    role: str = Field(default="vendedor", description="Rol asignado: 'admin' o 'vendedor'", examples=["vendedor"])


class UsuarioLogin(BaseModel):
    """
    DTO utilizado para el proceso de login inicial del sistema.
    """
    username: str = Field(..., examples=["admin"])
    password: str = Field(..., examples=["admin123"])


# ==========================================
# 2. SCHEMAS PARA RESPUESTAS (RESPONSES)
# ==========================================

class UsuarioResponse(BaseModel):
    """
    DTO seguro para retornar la información del usuario al frontend.
    Omite deliberadamente cualquier campo relacionado con hashes de contraseñas.
    """
    id: int
    username: str
    role: str

    model_config = {
        "from_attributes": True
    }


class TokenResponse(BaseModel):
    """
    DTO para la devolución exitosa del token JWT tras la autenticación.
    """
    access_token: str
    token_type: str = "bearer"