from typing import List
from fastapi import Depends, HTTPException, status
from src.dependencies.auth import get_current_user
from src.models.usuario import Usuario

class RoleChecker:
    def __init__(self, roles_permitidos: List[str]):
        """
        Inicializa la dependencia con la lista de roles autorizados.
        Normaliza los roles permitidos a mayúsculas.
        """
        self.roles_permitidos = [role.upper() for role in roles_permitidos]

    def __call__(self, current_user: Usuario = Depends(get_current_user)) -> Usuario:
        """
        Evalúa si el usuario autenticado tiene un rol válido.
        Se ejecuta automáticamente al usarse como Depends().
        """
        # 🌟 Convertimos a mayúsculas el rol de la BD para que no falle por tipeo
        if current_user.role.upper() not in self.roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenés los privilegios necesarios para realizar esta acción."
            )
            
        return current_user