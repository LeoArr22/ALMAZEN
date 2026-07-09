from sqlalchemy.orm import Session
from typing import Optional
from src.models.usuario import Usuario
from src.schemas.usuario_schema import UsuarioCreate

class UsuarioRepository:

    @staticmethod
    def obtener_por_username(db: Session, username: str) -> Optional[Usuario]:
        """
        Busca un usuario en la base de datos basándose en su nombre de usuario único.
        Esencial para el proceso de login y validación de tokens en la dependencia.
        """
        return db.query(Usuario).filter(Usuario.username == username).first()

    @staticmethod
    def obtener_por_id(db: Session, usuario_id: int) -> Optional[Usuario]:
        """
        Busca un usuario utilizando su clave primaria.
        Esencial para resolver la inyección de dependencias en las rutas protegidas.
        """
        return db.query(Usuario).filter(Usuario.id == usuario_id).first()

    @staticmethod
    def crear(db: Session, usuario_in: UsuarioCreate, password_hasheado: str) -> Usuario:
        """
        Inserta un nuevo usuario en la sesión de SQLAlchemy.
        Recibe la contraseña ya hasheada desde la capa de servicio y no ejecuta commit.
        """
        nuevo_usuario = Usuario(
            username=usuario_in.username,
            password_hashed=password_hasheado,  # Guardamos el hash seguro
            role=usuario_in.role
        )
        db.add(nuevo_usuario)
        db.flush()  # Genera el ID en memoria dentro de la transacción activa
        return nuevo_usuario