
"""
Order Management Service
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import uuid
import logging

from app.models.order import (
    Order, OrderItem, OrderStatus, PaymentStatus, OrderStatusHistory,
    OrderRefund, OrderInventoryReservation, OrderNotification
)
from app.models.cart import Cart, CartItem
from app.models.product import Product, ProductVariant
from app.models.user import User
from app.schemas.order import (
    OrderCreate, OrderStatusUpdate, OrderRefundCreate, OrderSearchFilters
)
from app.services.cart_service import CartService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class OrderService:
    """Order management service"""
    
    # Order number generation
    ORDER_PREFIX = "ORD"
    REFUND_PREFIX = "REF"
    
    # Inventory reservation duration (minutes)
    INVENTORY_RESERVATION_DURATION = 30
    
    @classmethod
    def create_order(cls, db: Session, order_data: OrderCreate, user_id: Optional[int] = None) -> Order:
        """Create order from cart or items"""
        
        # Generate order number
        order_number = cls._generate_order_number(db)
        
        # Validate and get items
        if order_data.cart_id:
            cart_items = cls._get_cart_items(db, order_data.cart_id, user_id)
        else:
            cart_items = cls._validate_order_items(db, order_data.items)
        
        if not cart_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid items found for order"
            )
        
        # Reserve inventory
        reservations = cls._reserve_inventory(db, cart_items, order_number)
        
        try:
            # Calculate pricing
            pricing = cls._calculate_order_pricing(cart_items)
            
            # Prepare addresses
            shipping_address = order_data.shipping_address or order_data.billing_address
            
            # Create order
            order = Order(
                order_number=order_number,
                user_id=user_id,
                guest_email=order_data.guest_email,
                guest_phone=order_data.guest_phone,
                status=OrderStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                subtotal=pricing['subtotal'],
                discount_amount=pricing['discount'],
                tax_amount=pricing['tax'],
                shipping_cost=pricing['shipping'],
                total=pricing['total'],
                billing_address=order_data.billing_address.dict(),
                shipping_address=shipping_address.dict(),
                customer_notes=order_data.customer_notes,
                order_source="web"
            )
            
            db.add(order)
            db.flush()  # Get order ID
            
            # Create order items
            order_items = []
            for cart_item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=cart_item['product_id'],
                    variant_id=cart_item.get('variant_id'),
                    product_name=cart_item['product_name'],
                    product_sku=cart_item.get('product_sku'),
                    variant_options=cart_item.get('variant_options'),
                    unit_price=cart_item['unit_price'],
                    discount_amount=cart_item['discount_amount'],
                    final_price=cart_item['final_price'],
                    quantity=cart_item['quantity'],
                    custom_options=cart_item.get('custom_options'),
                    notes=cart_item.get('notes')
                )
                order_items.append(order_item)
                db.add(order_item)
            
            # Create status history
            cls._add_status_history(db, order.id, None, OrderStatus.PENDING, user_id, "Order created")
            
            # Update reservations with order ID
            for reservation in reservations:
                reservation.order_id = order.id
            
            # Clear cart if order was created from cart
            if order_data.cart_id and user_id:
                CartService.clear_cart(db, order_data.cart_id, user_id)
            
            db.commit()
            
            # Send order confirmation email
            cls._send_order_confirmation(db, order)
            
            logger.info(f"Order created: {order_number} for user: {user_id}")
            return order
            
        except Exception as e:
            # Release reservations on error
            cls._release_reservations(db, reservations)
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create order: {str(e)}"
            )
    
    @classmethod
    def get_order(cls, db: Session, order_id: int, user_id: Optional[int] = None) -> Optional[Order]:
        """Get order by ID with access control"""
        query = db.query(Order).options(
            joinedload(Order.items),
            joinedload(Order.status_history)
        ).filter(Order.id == order_id)
        
        # Apply user filter for non-admin users
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_admin:
                query = query.filter(Order.user_id == user_id)
        
        return query.first()
    
    @classmethod
    def get_orders(
        cls, 
        db: Session, 
        filters: OrderSearchFilters,
        skip: int = 0, 
        limit: int = 50,
        user_id: Optional[int] = None
    ) -> Tuple[List[Order], int]:
        """Get orders with filtering and pagination"""
        
        query = db.query(Order).options(joinedload(Order.items))
        
        # Apply user filter for non-admin users
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_admin:
                query = query.filter(Order.user_id == user_id)
        
        # Apply filters
        if filters.status:
            query = query.filter(Order.status == filters.status)
        
        if filters.payment_status:
            query = query.filter(Order.payment_status == filters.payment_status)
        
        if filters.user_id:
            query = query.filter(Order.user_id == filters.user_id)
        
        if filters.order_number:
            query = query.filter(Order.order_number.ilike(f"%{filters.order_number}%"))
        
        if filters.date_from:
            query = query.filter(Order.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Order.created_at <= filters.date_to)
        
        if filters.min_amount:
            query = query.filter(Order.total >= filters.min_amount)
        
        if filters.max_amount:
            query = query.filter(Order.total <= filters.max_amount)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        orders = query.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
        
        return orders, total
    
    @classmethod
    def update_order_status(
        cls, 
        db: Session, 
        order_id: int, 
        status_update: OrderStatusUpdate,
        user_id: int
    ) -> Order:
        """Update order status with history tracking"""
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Validate status transition
        if not cls._is_valid_status_transition(order.status, status_update.status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {order.status} to {status_update.status}"
            )
        
        old_status = order.status
        
        # Update order status
        order.status = status_update.status
        order.updated_at = datetime.utcnow()
        
        # Update specific fields based on status
        if status_update.status == OrderStatus.SHIPPED:
            order.shipped_at = datetime.utcnow()
            if status_update.tracking_number:
                order.tracking_number = status_update.tracking_number
        
        elif status_update.status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.utcnow()
            if not order.shipped_at:
                order.shipped_at = datetime.utcnow()
        
        elif status_update.status == OrderStatus.CANCELLED:
            # Release inventory reservations
            cls._release_order_inventory(db, order)
        
        # Add status history
        cls._add_status_history(
            db, order_id, old_status, status_update.status, 
            user_id, status_update.reason, status_update.notes
        )
        
        db.commit()
        
        # Send status update notification
        cls._send_status_update_notification(db, order, old_status, status_update.status)
        
        logger.info(f"Order {order.order_number} status updated: {old_status} -> {status_update.status}")
        return order
    
    @classmethod
    def create_refund(
        cls, 
        db: Session, 
        order_id: int, 
        refund_data: OrderRefundCreate,
        user_id: int
    ) -> OrderRefund:
        """Create order refund"""
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if not order.can_be_refunded:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order cannot be refunded"
            )
        
        # Validate refund amount
        existing_refunds = db.query(func.sum(OrderRefund.amount)).filter(
            and_(
                OrderRefund.order_id == order_id,
                OrderRefund.status.in_(["approved", "processed"])
            )
        ).scalar() or 0
        
        if existing_refunds + refund_data.amount > order.total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund amount exceeds order total"
            )
        
        # Generate refund number
        refund_number = cls._generate_refund_number(db)
        
        # Create refund
        refund = OrderRefund(
            order_id=order_id,
            refund_number=refund_number,
            amount=refund_data.amount,
            reason=refund_data.reason,
            customer_notes=refund_data.customer_notes,
            status="pending"
        )
        
        db.add(refund)
        db.commit()
        
        # Send refund request notification
        cls._send_refund_notification(db, order, refund)
        
        logger.info(f"Refund created: {refund_number} for order: {order.order_number}")
        return refund
    
    @classmethod
    def _generate_order_number(cls, db: Session) -> str:
        """Generate unique order number"""
        while True:
            timestamp = datetime.utcnow().strftime("%Y%m%d")
            random_part = str(uuid.uuid4().int)[:6]
            order_number = f"{cls.ORDER_PREFIX}{timestamp}{random_part}"
            
            existing = db.query(Order).filter(Order.order_number == order_number).first()
            if not existing:
                return order_number
    
    @classmethod
    def _generate_refund_number(cls, db: Session) -> str:
        """Generate unique refund number"""
        while True:
            timestamp = datetime.utcnow().strftime("%Y%m%d")
            random_part = str(uuid.uuid4().int)[:6]
            refund_number = f"{cls.REFUND_PREFIX}{timestamp}{random_part}"
            
            existing = db.query(OrderRefund).filter(OrderRefund.refund_number == refund_number).first()
            if not existing:
                return refund_number
    
    @classmethod
    def _get_cart_items(cls, db: Session, cart_id: int, user_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get and validate cart items"""
        cart = CartService.get_cart(db, cart_id, user_id)
        if not cart or not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty or not found"
            )
        
        # Validate cart items and return formatted data
        validated_items = []
        for item in cart.items:
            # Check product availability
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product or not product.is_active:
                continue
            
            # Check stock availability
            if item.variant_id:
                variant = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first()
                if not variant or variant.stock_quantity < item.quantity:
                    continue
                available_stock = variant.stock_quantity
            else:
                if product.stock_quantity < item.quantity:
                    continue
                available_stock = product.stock_quantity
            
            validated_items.append({
                'product_id': item.product_id,
                'variant_id': item.variant_id,
                'product_name': item.product_name,
                'product_sku': item.product_sku,
                'variant_options': item.variant_options,
                'unit_price': item.unit_price,
                'discount_amount': item.discount_amount,
                'final_price': item.final_price,
                'quantity': item.quantity,
                'custom_options': item.custom_options,
                'notes': item.notes,
                'available_stock': available_stock
            })
        
        return validated_items
    
    @classmethod
    def _validate_order_items(cls, db: Session, items: List) -> List[Dict[str, Any]]:
        """Validate direct order items"""
        validated_items = []
        
        for item_data in items:
            # Get product
            product = db.query(Product).filter(Product.id == item_data.product_id).first()
            if not product or not product.is_active:
                continue
            
            # Get variant if specified
            variant = None
            if item_data.variant_id:
                variant = db.query(ProductVariant).filter(ProductVariant.id == item_data.variant_id).first()
                if not variant:
                    continue
            
            # Check stock
            available_stock = variant.stock_quantity if variant else product.stock_quantity
            if available_stock < item_data.quantity:
                continue
            
            # Calculate pricing
            unit_price = variant.price if variant else product.price
            discount_amount = 0  # Calculate based on discounts
            final_price = unit_price - discount_amount
            
            validated_items.append({
                'product_id': item_data.product_id,
                'variant_id': item_data.variant_id,
                'product_name': product.name,
                'product_sku': variant.sku if variant else product.sku,
                'variant_options': variant.options if variant else None,
                'unit_price': unit_price,
                'discount_amount': discount_amount,
                'final_price': final_price,
                'quantity': item_data.quantity,
                'custom_options': item_data.custom_options,
                'notes': item_data.notes,
                'available_stock': available_stock
            })
        
        return validated_items
    
    @classmethod
    def _reserve_inventory(cls, db: Session, items: List[Dict[str, Any]], order_number: str) -> List[OrderInventoryReservation]:
        """Reserve inventory for order items"""
        reservations = []
        expiry_time = datetime.utcnow() + timedelta(minutes=cls.INVENTORY_RESERVATION_DURATION)
        
        for item in items:
            reservation = OrderInventoryReservation(
                order_id=None,  # Will be set after order creation
                product_id=item['product_id'],
                variant_id=item.get('variant_id'),
                quantity_reserved=item['quantity'],
                expires_at=expiry_time,
                is_active=True
            )
            
            reservations.append(reservation)
            db.add(reservation)
        
        db.flush()
        return reservations
    
    @classmethod
    def _calculate_order_pricing(cls, items: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate order pricing"""
        subtotal = sum(item['final_price'] * item['quantity'] for item in items)
        discount = sum(item['discount_amount'] * item['quantity'] for item in items)
        
        # Calculate tax (18% GST for India)
        tax_rate = 0.18
        tax = subtotal * tax_rate
        
        # Calculate shipping (free for orders above ₹500)
        shipping = 0 if subtotal >= 500 else 50
        
        total = subtotal + tax + shipping
        
        return {
            'subtotal': subtotal,
            'discount': discount,
            'tax': tax,
            'shipping': shipping,
            'total': total
        }
    
    @classmethod
    def _add_status_history(
        cls, 
        db: Session, 
        order_id: int, 
        from_status: Optional[str], 
        to_status: str,
        user_id: Optional[int],
        reason: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """Add order status history entry"""
        history = OrderStatusHistory(
            order_id=order_id,
            from_status=from_status,
            to_status=to_status,
            changed_by_user_id=user_id,
            changed_by_type="admin" if user_id else "system",
            reason=reason,
            notes=notes
        )
        
        db.add(history)
    
    @classmethod
    def _is_valid_status_transition(cls, current_status: str, new_status: str) -> bool:
        """Validate status transition"""
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
            OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED, OrderStatus.RETURNED],
            OrderStatus.DELIVERED: [OrderStatus.RETURNED, OrderStatus.REFUNDED],
            OrderStatus.CANCELLED: [],  # Terminal state
            OrderStatus.RETURNED: [OrderStatus.REFUNDED],
            OrderStatus.REFUNDED: []  # Terminal state
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    @classmethod
    def _release_reservations(cls, db: Session, reservations: List[OrderInventoryReservation]):
        """Release inventory reservations"""
        for reservation in reservations:
            reservation.is_active = False
            reservation.released_at = datetime.utcnow()
    
    @classmethod
    def _release_order_inventory(cls, db: Session, order: Order):
        """Release inventory for cancelled order"""
        reservations = db.query(OrderInventoryReservation).filter(
            and_(
                OrderInventoryReservation.order_id == order.id,
                OrderInventoryReservation.is_active == True
            )
        ).all()
        
        cls._release_reservations(db, reservations)
    
    @classmethod
    def _send_order_confirmation(cls, db: Session, order: Order):
        """Send order confirmation email"""
        try:
            email_service = EmailService()
            recipient = order.user.email if order.user else order.guest_email
            
            if recipient:
                email_service.send_order_confirmation(
                    email=recipient,
                    order_number=order.order_number,
                    total=float(order.total),
                    items=order.items
                )
        except Exception as e:
            logger.error(f"Failed to send order confirmation: {str(e)}")
    
    @classmethod
    def _send_status_update_notification(cls, db: Session, order: Order, old_status: str, new_status: str):
        """Send order status update notification"""
        try:
            email_service = EmailService()
            recipient = order.user.email if order.user else order.guest_email
            
            if recipient:
                email_service.send_order_status_update(
                    email=recipient,
                    order_number=order.order_number,
                    status=new_status,
                    tracking_number=order.tracking_number
                )
        except Exception as e:
            logger.error(f"Failed to send status update notification: {str(e)}")
    
    @classmethod
    def _send_refund_notification(cls, db: Session, order: Order, refund: OrderRefund):
        """Send refund notification"""
        try:
            email_service = EmailService()
            recipient = order.user.email if order.user else order.guest_email
            
            if recipient:
                email_service.send_refund_notification(
                    email=recipient,
                    order_number=order.order_number,
                    refund_number=refund.refund_number,
                    amount=float(refund.amount)
                )
        except Exception as e:
            logger.error(f"Failed to send refund notification: {str(e)}")
