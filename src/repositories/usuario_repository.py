from sqlalchemy.orm import Session
from typing import Optional, List
from src.models.usuario import Usuario
from src.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate

class UsuarioRepository:

    @staticmethod
    def obtener_por_username(db: Session, username: str) -> Optional[Usuario]:
        return db.query(Usuario).filter(Usuario.username == username).first()

    @staticmethod
    def obtener_por_id(db: Session, usuario_id: int) -> Optional[Usuario]:
        return db.query(Usuario).filter(Usuario.id == usuario_id).first()

    @staticmethod
    def obtener_todos(db: Session) -> List[Usuario]:
        return db.query(Usuario).order_by(Usuario.id.asc()).all()

    @staticmethod
    def crear(db: Session, usuario_in: UsuarioCreate, password_hasheado: str) -> Usuario:
        nuevo_usuario = Usuario(
            username=usuario_in.username,
            password_hashed=password_hasheado,
            role=usuario_in.role,
            activo=True
        )
        db.add(nuevo_usuario)
        db.flush()
        return nuevo_usuario

    @staticmethod
    def actualizar(db: Session, usuario_db: Usuario, datos: dict) -> Usuario:
        for campo, valor in datos.items():
            setattr(usuario_db, campo, valor)
        db.flush()
        return usuario_db