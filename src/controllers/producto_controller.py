from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.schemas.producto_schema import ProductoCreate, ProductoResponse, ProductoUpdate
from src.services.producto_service import ProductoService

# 🛡️ IMPORTACIONES DE SEGURIDAD Y ROLES
from src.dependencies.roles import RoleChecker
from src.models.usuario import Usuario

router = APIRouter(prefix="/productos", tags=["Productos"])
solo_admin = RoleChecker(["ADMIN", "admin"])

# 🛡️ PROTEGIDO: Solo admin crea productos nuevos
@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(
    producto_in: ProductoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)  # 👈 Inyección de rol
):
    """Crea un nuevo producto en el catálogo."""
    return ProductoService.crear_producto(db, producto_in)

# 🔓 LIBRE: El vendedor necesita consultar la lista de productos
@router.get("/", response_model=list[ProductoResponse])
def listar_productos(skip: int = 0, limit: int = 500, db: Session = Depends(get_db)):
    """Trae la lista completa de productos paginada."""
    return ProductoService.listar_productos(db, skip, limit)

# 🔓 LIBRE: Para mostrar alertas visuales en el sistema de stock
@router.get("/bajo-stock", response_model=list[ProductoResponse])
def verificar_alerta_stock(limite: int = 5, db: Session = Depends(get_db)):
    """Trae los productos que tengan un stock menor o igual al límite especificado."""
    return ProductoService.verificar_alerta_stock(db, limite)

# 🔓 LIBRE: Indispensable para el lector de código de barras en el punto de venta
@router.get("/codigo/{codigo_barras}", response_model=ProductoResponse)
def obtener_producto_por_codigo(codigo_barras: str, db: Session = Depends(get_db)):
    """Busca un producto específico utilizando su código de barras."""
    return ProductoService.obtener_por_codigo(db, codigo_barras)

# 🔓 LIBRE: Indispensable para el buscador por texto del POS
@router.get("/buscar", response_model=list[ProductoResponse])
def buscar_por_nombre(nombre: str, db: Session = Depends(get_db)):
    """Busca productos cuyo nombre coincida parcialmente (no distingue mayúsculas)."""
    return ProductoService.buscar_por_nombre(db, nombre)

# 🔓 LIBRE: Para filtrar productos dinámicamente en la interfaz
@router.get("/categoria/{categoria}", response_model=list[ProductoResponse])
def buscar_por_categoria(categoria: str, db: Session = Depends(get_db)):
    """Filtra productos por su categoría."""
    return ProductoService.buscar_por_categoria(db, categoria)

# 🔓 LIBRE: Consulta individual estándar
@router.get("/{producto_id}", response_model=ProductoResponse)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    """Busca un producto específico por su ID."""
    return ProductoService.obtener_producto(db, producto_id)

# 🛡️ PROTEGIDO: Solo el admin puede modificar precios, stock o datos
@router.put("/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(
    producto_id: int, 
    producto_in: ProductoUpdate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)  # 👈 Inyección de rol
):
    """Actualiza los datos o el stock de un producto."""
    return ProductoService.modificar_producto(db, producto_id, producto_in)

# 🛡️ PROTEGIDO: El borrado físico o lógico de mercadería queda restringido al dueño
@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(
    producto_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)  # 👈 Inyección de rol
):
    """Elimina permanentemente un producto del catálogo."""
    return ProductoService.borrar_producto(db, producto_id)