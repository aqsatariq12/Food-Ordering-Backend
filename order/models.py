from django.db import models
from restaurants.models import Restaurants, MenuItem, Deal,User
from django.core.exceptions import ValidationError
# Create your models here.


class Payment(models.Model):
    CHOICE_FIELDS_PAY_STATUS = (
        ('pending','PENDING'),
        ('success','SUCCESS'),
        ('failed','FAILED'),
        ( 'refunded','REFUNDED')
    )
    CHOICE_FIELDS_PAY_METHOD = (
        ('cash', 'CASH ON DELIVERY'),
        ('stripe','STRIPE'),
        ('jazzcash', 'JAZZCASH'),
        ('easypaisa','EASYPAISA')
    )

    user =  models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=120, choices=CHOICE_FIELDS_PAY_STATUS, default='pending')
    payment_method =models.CharField(max_length=120, choices=CHOICE_FIELDS_PAY_METHOD,default='cash')
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Payment {self.id} - {self.payment_status}'
    
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Cart of {self.user.email}'
    
    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null= True, blank=True)
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [("cart","menu_item"),("cart","deal")]
    
    def clean(self):
        if not self.menu_item and not self.deal:
            raise ValidationError('A cart item must have either a menu item or a deal.')
    
    @property
    def subtotal(self):
        if self.menu_item:
            return self.menu_item.price * self.quantity
        if self.deal:
            return self.deal.combo_price * self.quantity
        return 0
    
    def __str__(self):
        item = self.menu_item.name if self.menu_item else self.deal.name
        return f'{self.quantity} X {item}'
    

class Order(models.Model):
    CHOICE_FIELDS_ORDER_STATUS = (
        ('pending','PENDING'),
        ('accepted','ACCEPTED'),
        ('preparing','PREPARING'),
        ( 'out_for_delivery','OUT FOR DELIVERY'),
        ('delivered','DELIVERED'),
        ('cancelled','CANCELLED')
    )

    user =  models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='orders')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, related_name='orders', null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_status = models.CharField(max_length=120, choices=CHOICE_FIELDS_ORDER_STATUS, default='pending')
    delivery_address =  models.CharField(max_length=255, null=True, blank=True)
    created_at =  models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.restaurant.name} - {self.current_status}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item =  models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, blank=True)
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        if not self.menu_item and not self.deal:
            raise ValidationError("An order item must have either a menu item or a deal.")
    
    @property
    def subtotal(self):
        return self.price_at_order * self.quantity

    def __str__(self):
        if self.menu_item:
            item = self.menu_item.name
        elif self.deal:
            item = self.deal.name
        else:
            item = "Unknown Item"

        return f"{self.quantity} x {item}"

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=120, choices=Order.CHOICE_FIELDS_ORDER_STATUS)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_status_changes")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name_plural = "Order status histories"
    
    def __str__(self):
        return f"Order #{self.order.id} - {self.status}"