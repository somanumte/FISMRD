# ============================================
# MODELO DE SERIALES DE FABRICANTE
# ============================================
# Sistema de tracking de números de serie individuales
# Permite trazabilidad completa: qué serial se vendió en qué factura

from app import db
from app.models.mixins import TimestampMixin
from datetime import datetime, date
from enum import Enum


class SerialStatus(Enum):
    """Estados posibles de un serial"""
    AVAILABLE = 'available'      # Disponible para venta
    RESERVED = 'reserved'        # Reservado (en proceso de venta)
    SOLD = 'sold'                # Vendido
    DAMAGED = 'damaged'          # Dañado/defectuoso
    RETURNED = 'returned'        # Devuelto por cliente
    IN_REPAIR = 'in_repair'      # En reparación
    LOST = 'lost'                # Perdido/extraviado


# Lista de estados para usar en formularios
SERIAL_STATUS_CHOICES = [
    ('available', 'Disponible'),
    ('reserved', 'Reservado'),
    ('sold', 'Vendido'),
    ('damaged', 'Dañado'),
    ('returned', 'Devuelto'),
    ('in_repair', 'En Reparación'),
    ('lost', 'Perdido'),
]


class LaptopSerial(TimestampMixin, db.Model):
    """
    Modelo para almacenar números de serie individuales de fabricante.
    
    Cada laptop física tiene UN serial único del fabricante.
    Un modelo de laptop (Laptop) puede tener MÚLTIPLES seriales
    (cuando hay varias unidades del mismo modelo).
    
    Ejemplo:
        - Laptop: Dell XPS 15 (SKU: LX-20250122-0001, quantity: 3)
        - Seriales:
            - ABC123XYZ (Dell Service Tag)
            - DEF456UVW (Dell Service Tag)
            - GHI789RST (Dell Service Tag)
    """
    __tablename__ = 'laptop_serials'
    
    # ===== IDENTIFICADORES =====
    id = db.Column(db.Integer, primary_key=True)
    
    # Número de serie del fabricante (único globalmente)
    serial_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # Serial normalizado (para búsquedas - sin espacios, uppercase)
    serial_normalized = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # ===== RELACIÓN CON LAPTOP =====
    laptop_id = db.Column(db.Integer, db.ForeignKey('laptops.id', ondelete='CASCADE'), nullable=False, index=True)
    laptop = db.relationship('Laptop', backref=db.backref('serials', lazy='dynamic', cascade='all, delete-orphan'))
    
    # ===== ESTADO =====
    status = db.Column(db.String(20), nullable=False, default='available', index=True)
    
    # ===== INFORMACIÓN ADICIONAL =====
    # Tipo de serial (para diferentes fabricantes)
    serial_type = db.Column(db.String(50), nullable=True, default='manufacturer')
    # Opciones: 'manufacturer', 'service_tag', 'product_id', 'imei', 'mac_address', 'custom'
    
    # Código de barras asociado (si es diferente al serial)
    barcode = db.Column(db.String(100), nullable=True, index=True)
    
    # Notas específicas de esta unidad
    notes = db.Column(db.Text, nullable=True)
    
    # ===== INFORMACIÓN DE COMPRA (por unidad) =====
    # Costo de compra específico de esta unidad (si difiere del modelo)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=True)
    
    # Fecha de ingreso de esta unidad específica
    received_date = db.Column(db.Date, nullable=True, default=date.today)
    
    # ===== GARANTÍA =====
    warranty_start = db.Column(db.Date, nullable=True)
    warranty_end = db.Column(db.Date, nullable=True)
    warranty_provider = db.Column(db.String(100), nullable=True)
    
    # ===== TRAZABILIDAD DE VENTA =====
    # Se llena cuando el serial se vende
    sold_date = db.Column(db.DateTime, nullable=True)
    sold_price = db.Column(db.Numeric(12, 2), nullable=True)
    
    # ===== AUDITORÍA =====
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    
    # ===== PROPIEDADES =====
    
    @property
    def is_available(self):
        """Verifica si el serial está disponible para venta"""
        return self.status == 'available'
    
    @property
    def is_sold(self):
        """Verifica si el serial está vendido"""
        return self.status == 'sold'
    
    @property
    def status_display(self):
        """Nombre legible del estado"""
        status_names = dict(SERIAL_STATUS_CHOICES)
        return status_names.get(self.status, self.status)
    
    @property
    def status_badge_class(self):
        """Clase CSS para el badge de estado"""
        classes = {
            'available': 'bg-green-100 text-green-800',
            'reserved': 'bg-yellow-100 text-yellow-800',
            'sold': 'bg-blue-100 text-blue-800',
            'damaged': 'bg-red-100 text-red-800',
            'returned': 'bg-purple-100 text-purple-800',
            'in_repair': 'bg-orange-100 text-orange-800',
            'lost': 'bg-gray-100 text-gray-800',
        }
        return classes.get(self.status, 'bg-gray-100 text-gray-800')
    
    @property
    def has_warranty(self):
        """Verifica si tiene garantía activa"""
        if self.warranty_end:
            return date.today() <= self.warranty_end
        return False
    
    @property
    def warranty_days_remaining(self):
        """Días restantes de garantía"""
        if self.warranty_end:
            delta = self.warranty_end - date.today()
            return max(0, delta.days)
        return None
    
    @property
    def effective_cost(self):
        """Costo efectivo (el de la unidad o el del modelo)"""
        if self.unit_cost:
            return float(self.unit_cost)
        if self.laptop:
            return float(self.laptop.purchase_cost)
        return 0
    
    # ===== MÉTODOS =====
    
    def mark_as_sold(self, price=None):
        """
        Marca el serial como vendido
        
        Args:
            price: Precio de venta (opcional, se usa el del laptop si no se provee)
        """
        self.status = 'sold'
        self.sold_date = datetime.utcnow()
        if price:
            self.sold_price = price
        elif self.laptop:
            self.sold_price = self.laptop.effective_price
    
    def mark_as_available(self):
        """Restaura el serial a disponible (para devoluciones)"""
        self.status = 'available'
        self.sold_date = None
        self.sold_price = None
    
    def reserve(self):
        """Reserva el serial temporalmente"""
        if self.status == 'available':
            self.status = 'reserved'
            return True
        return False
    
    def release_reservation(self):
        """Libera una reserva"""
        if self.status == 'reserved':
            self.status = 'available'
            return True
        return False
    
    @staticmethod
    def normalize_serial(serial):
        """
        Normaliza un número de serie para búsquedas consistentes
        
        Args:
            serial: Número de serie original
            
        Returns:
            str: Serial normalizado (uppercase, sin espacios)
        """
        if not serial:
            return None
        # Remover espacios, guiones y convertir a mayúsculas
        normalized = serial.strip().upper()
        # Remover caracteres especiales comunes en códigos de barras
        normalized = normalized.replace(' ', '').replace('-', '').replace('_', '')
        return normalized
    
    def to_dict(self, include_laptop=True):
        """Serializa a diccionario"""
        data = {
            'id': self.id,
            'serial_number': self.serial_number,
            'serial_normalized': self.serial_normalized,
            'laptop_id': self.laptop_id,
            'status': self.status,
            'status_display': self.status_display,
            'serial_type': self.serial_type,
            'barcode': self.barcode,
            'notes': self.notes,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'warranty_start': self.warranty_start.isoformat() if self.warranty_start else None,
            'warranty_end': self.warranty_end.isoformat() if self.warranty_end else None,
            'warranty_provider': self.warranty_provider,
            'has_warranty': self.has_warranty,
            'warranty_days_remaining': self.warranty_days_remaining,
            'sold_date': self.sold_date.isoformat() if self.sold_date else None,
            'sold_price': float(self.sold_price) if self.sold_price else None,
            'is_available': self.is_available,
            'is_sold': self.is_sold,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_laptop and self.laptop:
            data['laptop'] = {
                'id': self.laptop.id,
                'sku': self.laptop.sku,
                'display_name': self.laptop.display_name,
                'brand': self.laptop.brand.name if self.laptop.brand else None,
                'model': self.laptop.model.name if self.laptop.model else None,
            }
        
        return data
    
    def __repr__(self):
        return f'<LaptopSerial {self.serial_number} - {self.status}>'
    
    # ===== ÍNDICES COMPUESTOS =====
    __table_args__ = (
        db.Index('idx_serial_laptop_status', 'laptop_id', 'status'),
        db.Index('idx_serial_status', 'status'),
        db.Index('idx_serial_barcode', 'barcode'),
    )


# ============================================
# MODELO: RELACIÓN SERIAL - FACTURA
# ============================================
# Registra qué seriales se vendieron en cada item de factura

class InvoiceItemSerial(TimestampMixin, db.Model):
    """
    Tabla de relación entre InvoiceItem y LaptopSerial.
    
    Permite saber exactamente qué seriales se incluyeron en cada
    línea de factura, proporcionando trazabilidad completa.
    
    Ejemplo:
        - InvoiceItem: Dell XPS 15, cantidad: 2
        - Seriales vendidos:
            - ABC123XYZ
            - DEF456UVW
    """
    __tablename__ = 'invoice_item_serials'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relación con item de factura
    invoice_item_id = db.Column(
        db.Integer, 
        db.ForeignKey('invoice_items.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    # Relación con serial
    serial_id = db.Column(
        db.Integer, 
        db.ForeignKey('laptop_serials.id', ondelete='RESTRICT'),  # No permitir borrar si está en factura
        nullable=False,
        index=True
    )
    
    # Precio de venta de esta unidad específica (puede diferir del unit_price del item)
    unit_sale_price = db.Column(db.Numeric(12, 2), nullable=True)
    
    # Notas específicas de esta unidad en la venta
    notes = db.Column(db.Text, nullable=True)
    
    # Relaciones
    invoice_item = db.relationship('InvoiceItem', backref=db.backref(
        'sold_serials', 
        lazy='dynamic', 
        cascade='all, delete-orphan'
    ))
    serial = db.relationship('LaptopSerial', backref=db.backref(
        'sales_history', 
        lazy='dynamic'
    ))
    
    def to_dict(self):
        """Serializa a diccionario"""
        return {
            'id': self.id,
            'invoice_item_id': self.invoice_item_id,
            'serial_id': self.serial_id,
            'serial_number': self.serial.serial_number if self.serial else None,
            'unit_sale_price': float(self.unit_sale_price) if self.unit_sale_price else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<InvoiceItemSerial Item:{self.invoice_item_id} Serial:{self.serial_id}>'
    
    __table_args__ = (
        # Un serial solo puede estar en un item de factura (evitar duplicados)
        db.UniqueConstraint('serial_id', 'invoice_item_id', name='uq_serial_invoice_item'),
        db.Index('idx_invoice_item_serial', 'invoice_item_id', 'serial_id'),
    )


# ============================================
# MODELO: HISTORIAL DE MOVIMIENTOS DE SERIAL
# ============================================
# Para auditoría completa de cada serial

class SerialMovement(TimestampMixin, db.Model):
    """
    Registro de todos los movimientos/cambios de estado de un serial.
    
    Proporciona auditoría completa de la vida de cada unidad:
    - Ingreso al inventario
    - Reservas
    - Ventas
    - Devoluciones
    - Cambios de estado
    """
    __tablename__ = 'serial_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Serial relacionado
    serial_id = db.Column(
        db.Integer, 
        db.ForeignKey('laptop_serials.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    # Tipo de movimiento
    movement_type = db.Column(db.String(30), nullable=False, index=True)
    # Opciones: 'created', 'status_change', 'sold', 'returned', 'reserved', 
    #           'released', 'damaged', 'repaired', 'transferred', 'adjustment'
    
    # Estados antes y después
    previous_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=True)
    
    # Referencias opcionales
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    
    # Descripción del movimiento
    description = db.Column(db.Text, nullable=True)
    
    # Datos adicionales (JSON) - No usar 'metadata' que es reservado en SQLAlchemy
    extra_data = db.Column(db.JSON, nullable=True)
    
    # Usuario que realizó el movimiento
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', foreign_keys=[user_id])
    
    # Relaciones
    serial = db.relationship('LaptopSerial', backref=db.backref(
        'movements', 
        lazy='dynamic',
        order_by='desc(SerialMovement.created_at)'
    ))
    invoice = db.relationship('Invoice', backref=db.backref('serial_movements', lazy='dynamic'))
    
    def to_dict(self):
        """Serializa a diccionario"""
        return {
            'id': self.id,
            'serial_id': self.serial_id,
            'movement_type': self.movement_type,
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'invoice_id': self.invoice_id,
            'description': self.description,
            'extra_data': self.extra_data,
            'user': self.user.username if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<SerialMovement {self.movement_type} Serial:{self.serial_id}>'
    
    __table_args__ = (
        db.Index('idx_movement_serial_type', 'serial_id', 'movement_type'),
        db.Index('idx_movement_date', 'created_at'),
    )
