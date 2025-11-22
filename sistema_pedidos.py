"""
SISTEMA DE GESTIÓN DE PEDIDOS
Aplica: Patrón Repository, SOLID e Inyección de Dependencias
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict

# ========== MODELOS ==========
@dataclass
class Product:
    id: int
    name: str
    price: float
    stock: int

@dataclass
class OrderItem:
    product: Product
    quantity: int
    
    @property
    def subtotal(self) -> float:
        return self.product.price * self.quantity

@dataclass
class Order:
    id: Optional[int]
    customer_name: str
    items: List[OrderItem]
    status: str = "pending"
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.items is None:
            self.items = []
    
    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)

# ========== INTERFACES (SOLID - ISP) ==========
class IOrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> None: 
        pass
    
    @abstractmethod
    def find_by_id(self, order_id: int) -> Optional[Order]: 
        pass
    
    @abstractmethod
    def find_all(self) -> List[Order]: 
        pass

class IProductRepository(ABC):
    @abstractmethod
    def find_by_id(self, product_id: int) -> Optional[Product]: 
        pass
    
    @abstractmethod
    def find_all(self) -> List[Product]: 
        pass
    
    @abstractmethod
    def update_stock(self, product_id: int, new_stock: int) -> None: 
        pass

class INotificationService(ABC):
    @abstractmethod
    def send_order_confirmation(self, order: Order) -> bool: 
        pass

# ========== REPOSITORIES (PATRÓN REPOSITORY) ==========
class InMemoryOrderRepository(IOrderRepository):
    def __init__(self):
        self._orders: Dict[int, Order] = {}
        self._next_id = 1
    
    def save(self, order: Order) -> None:
        if order.id is None:
            order.id = self._next_id
            self._next_id += 1
        self._orders[order.id] = order
        print(f"💾 Orden #{order.id} guardada en repositorio")
    
    def find_by_id(self, order_id: int) -> Optional[Order]:
        return self._orders.get(order_id)
    
    def find_all(self) -> List[Order]:
        return list(self._orders.values())

class InMemoryProductRepository(IProductRepository):
    def __init__(self):
        self._products: Dict[int, Product] = {
            1: Product(id=1, name="Laptop Gaming", price=1200.00, stock=5),
            2: Product(id=2, name="Mouse Inalámbrico", price=45.99, stock=20),
            3: Product(id=3, name="Teclado Mecánico", price=89.99, stock=15),
            4: Product(id=4, name="Monitor 24'", price=299.99, stock=8),
        }
    
    def find_by_id(self, product_id: int) -> Optional[Product]:
        product = self._products.get(product_id)
        if product:
            print(f"Producto encontrado: {product.name}")
        return product
    
    def find_all(self) -> List[Product]:
        return list(self._products.values())
    
    def update_stock(self, product_id: int, new_stock: int) -> None:
        if product_id in self._products:
            old_stock = self._products[product_id].stock
            self._products[product_id].stock = new_stock
            print(f"Stock actualizado: Producto {product_id} - {old_stock} → {new_stock}")

# ========== SERVICES (SOLID - OCP) ==========
class EmailNotificationService(INotificationService):
    def send_order_confirmation(self, order: Order) -> bool:
        print(f"\n EMAIL DE CONFIRMACIÓN")
        print(f"   Para: {order.customer_name}")
        print(f"   Asunto: Confirmación de Pedido #{order.id}")
        print(f"   Total: ${order.total:.2f}")
        print(f"   Estado: {order.status}")
        print(f"   ¡Gracias por tu compra!")
        return True

class SMSNotificationService(INotificationService):
    def send_order_confirmation(self, order: Order) -> bool:
        print(f"\n📱 SMS DE CONFIRMACIÓN")
        print(f"   Para: {order.customer_name}")
        print(f"   Mensaje: Pedido #{order.id} confirmado. Total: ${order.total:.2f}")
        return True

# ========== ORDER SERVICE (INYECCIÓN DE DEPENDENCIAS) ==========
class OrderService:
    # INYECCIÓN DE DEPENDENCIAS - Las dependencias inyectadas en el constructor
    def __init__(
        self, 
        order_repository: IOrderRepository,
        product_repository: IProductRepository, 
        notification_service: INotificationService
    ):
        self.order_repository = order_repository
        self.product_repository = product_repository
        self.notification_service = notification_service
        print("OrderService inicializado con inyección de dependencias")
    
    def create_order(self, customer_name: str, items: List[tuple]) -> Order:
        """Crea una nueva orden (SOLID - SRP)"""
        print(f"\n Creando orden para: {customer_name}")
        
        order_items = []
        
        # Validar productos y stock
        for product_id, quantity in items:
            product = self.product_repository.find_by_id(product_id)
            if not product:
                raise ValueError(f" Producto con ID {product_id} no encontrado")
            
            if product.stock < quantity:
                raise ValueError(
                    f" Stock insuficiente para {product.name}. "
                    f"Disponible: {product.stock}, Solicitado: {quantity}"
                )
            
            # Crear item de orden
            order_item = OrderItem(product=product, quantity=quantity)
            order_items.append(order_item)
            
            print(f"   Añadido: {quantity}x {product.name} - ${order_item.subtotal:.2f}")
            
            # Actualizar stock
            new_stock = product.stock - quantity
            self.product_repository.update_stock(product_id, new_stock)
        
        # Crear orden
        order = Order(id=None, customer_name=customer_name, items=order_items)
        
        # Guardar en repositorio
        self.order_repository.save(order)
        
        # Enviar notificación
        self.notification_service.send_order_confirmation(order)
        
        return order
    
    def get_order(self, order_id: int) -> Order:
        """Obtiene una orden por ID"""
        order = self.order_repository.find_by_id(order_id)
        if not order:
            raise ValueError(f" Orden con ID {order_id} no encontrada")
        return order
    
    def list_orders(self) -> List[Order]:
        """Lista todas las órdenes"""
        return self.order_repository.find_all()
    
    def get_available_products(self) -> List[Product]:
        """Obtiene productos disponibles"""
        return self.product_repository.find_all()

# ========== DEPENDENCY CONTAINER ==========
class DependencyContainer:
    """Contenedor de dependencias para gestión centralizada"""
    
    def __init__(self, notification_type: str = "email"):
        self.notification_type = notification_type
    
    def get_order_repository(self) -> IOrderRepository:
        return InMemoryOrderRepository()
    
    def get_product_repository(self) -> IProductRepository:
        return InMemoryProductRepository()
    
    def get_notification_service(self) -> INotificationService:
        if self.notification_type == "sms":
            return SMSNotificationService()
        else:
            return EmailNotificationService()
    
    def get_order_service(self) -> OrderService:
        return OrderService(
            order_repository=self.get_order_repository(),
            product_repository=self.get_product_repository(),
            notification_service=self.get_notification_service()
        )

# ========== EJECUCIÓN PRINCIPAL ==========
def main():
    print(" SISTEMA DE GESTIÓN DE PEDIDOS")
    print("=" * 50)
    print(" Aplicando: Patrón Repository, SOLID e Inyección de Dependencias")
    
    # CONFIGURACIÓN CON INYECCIÓN DE DEPENDENCIAS
    print("\n Configurando dependencias...")
    container = DependencyContainer(notification_type="email")
    order_service = container.get_order_service()
    
    # Mostrar productos disponibles
    print("\ PRODUCTOS DISPONIBLES:")
    products = order_service.get_available_products()
    for i, product in enumerate(products, 1):
        print(f"   {product.id}. {product.name}")
        print(f"      Precio: ${product.price:.2f} | Stock: {product.stock}")
    
    # Demo 1: Orden exitosa
    print("\n" + "="*50)
    print(" DEMO 1: ORDEN EXITOSA")
    print("="*50)
    
    try:
        order1 = order_service.create_order(
            customer_name="María González",
            items=[(1, 1), (2, 2), (4, 1)]  # 1 Laptop + 2 Mouses + 1 Monitor
        )
        
        print(f"\n ORDEN FINALIZADA EXITOSAMENTE!")
        print(f"   Número de orden: #{order1.id}")
        print(f"   Cliente: {order1.customer_name}")
        print(f"   Productos: {len(order1.items)}")
        print(f"   Total: ${order1.total:.2f}")
        
    except Exception as e:
        print(f" Error en orden 1: {e}")
    
    # Demo 2: Orden con error (stock insuficiente)
    print("\n" + "="*50)
    print(" DEMO 2: ORDEN CON ERROR")
    print("="*50)
    
    try:
        order2 = order_service.create_order(
            customer_name="Carlos Ruiz",
            items=[(1, 10)]  # Stock insuficiente
        )
    except Exception as e:
        print(f" {e}")
    
    # Demo 3: Listar órdenes existentes
    print("\n" + "="*50)
    print(" DEMO 3: LISTADO DE ÓRDENES")
    print("="*50)
    
    orders = order_service.list_orders()
    if orders:
        for order in orders:
            print(f"   Orden #{order.id}: {order.customer_name} - ${order.total:.2f} - {order.status}")
    else:
        print("   No hay órdenes registradas")
    
    print("\n" + "="*50)
    print(" DEMOSTRACIÓN COMPLETADA")
    print("="*50)

if __name__ == "__main__":
    main()