from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 
from src.config.database import engine, Base 

# 🌟 IMPORTACIÓN CRÍTICA DE MODELOS PARA SQLALCHEMY
from src.models.producto import Producto
from src.models.caja import Caja
from src.models.venta import Venta, VentaDetalle
from src.models.usuario import Usuario

# Controladores / Routers de la API JSON
from src.controllers import producto_controller, venta_controller, caja_controller, usuario_controller

# 🖥️ Router de la Interfaz Web HTML
from src.views.core_views import router_core
from src.views.producto_views import router_vistas_productos
from src.views.venta_views import router_vistas_ventas
from src.views.usuario_views import router_vistas_usuarios
from src.views.caja_views import router_vistas_cajas

# 🛡️ DEPENDENCIAS DE ROLES
from src.dependencies.roles import RoleChecker

# Inicialización de FastAPI
app = FastAPI(
    title="AlmaZen API & POS",
    description="Backend optimizado para control de stock, cajas y ventas con arquitectura limpia.",
    version="2.0.0"
)

# Creación automática de tablas si no existen al iniciar la app
Base.metadata.create_all(bind=engine)

# Configuración de Middlewares (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🎨 Servir archivos estáticos (CSS, JS, Imágenes)
app.mount("/static", StaticFiles(directory="static"), name="static")  

# Guardián para endpoints que requieran permisos elevados de administrador
solo_admin = RoleChecker(["ADMIN", "admin"])

# ==========================================
# 🖥️ ENRUTAMIENTO DE INTERFAZ WEB (HTML/UI)
# ==========================================
app.include_router(router_core)
app.include_router(router_vistas_productos)
app.include_router(router_vistas_ventas)
app.include_router(router_vistas_usuarios)
app.include_router(router_vistas_cajas)

# ==========================================
# 🔌 ENRUTAMIENTO DE LA API REST (JSON DATA)
# ==========================================
app.include_router(producto_controller.router)
app.include_router(caja_controller.router)
app.include_router(venta_controller.router) 
app.include_router(usuario_controller.router)