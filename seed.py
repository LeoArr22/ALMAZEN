# seed.py
import bcrypt  # <- Usamos la librería pura de Python/C
from sqlalchemy.orm import Session
from src.config.database import SessionLocal, engine, Base # 🌟 IMPORTAMOS EL engine Y EL Base ACÁ

# Cargamos los modelos para SQLAlchemy (¡Fundamental importarlos para que sepa qué tablas crear!)
from src.models.producto import Producto      
from src.models.venta import Venta, VentaDetalle
from src.models.caja import Caja
from src.models.usuario import Usuario

def crear_admin_inicial():
    print("🛠️ Creando el esqueleto de las tablas en la Base de Datos si no existen...")
    # 🌟 ESTA LÍNEA MÁGICA VA A CREAR LA TABLA "usuarios" Y TODAS LAS DEMÁS ANTES DE HACER EL SELECT
    Base.metadata.create_all(bind=engine)

    print("Iniciando la creación del usuario administrador con Bcrypt Nativo...")
    db = SessionLocal()
    try:
        # 1. Verificar si ya existe el admin (¡Ahora sí la tabla va a existir!)
        admin_existente = db.query(Usuario).filter(Usuario.username == "admin").first()
        if admin_existente:
            print("El usuario 'admin' ya existe en la base de datos.")
            return

        # 2. Hasheamos usando bcrypt puro sin intermediarios (passlib)
        password_plano = "admin123"
        # Convertimos el string a bytes, generamos la sal y hasheamos
        password_bytes = password_plano.encode('utf-8')
        salt = bcrypt.gensalt()
        password_seguro_bytes = bcrypt.hashpw(password_bytes, salt)
        
        # Lo volvemos a transformar a string (utf-8) para guardarlo en la columna String de la BD
        password_seguro_str = password_seguro_bytes.decode('utf-8')

        # 3. Crear el modelo e insertar
        nuevo_admin = Usuario(
            username="admin",
            password_hashed=password_seguro_str,
            role="ADMIN"
        )
        
        db.add(nuevo_admin)
        db.commit()
        print("¡Usuario 'admin' creado con éxito usando Bcrypt nativo!")
        print("Username: admin")
        print("Password: admin123")

    except Exception as e:
        db.rollback()
        print(f"Error al crear el administrador: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    crear_admin_inicial()