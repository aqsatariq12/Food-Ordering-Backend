from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory,Payment
# Register your models here.

@admin.register(Cart)
class  CartAdmin(admin.ModelAdmin):
    list_display = ['id','user','updated_at']

@admin.register(CartItem)
class  CartItemAdmin(admin.ModelAdmin):
    list_display = ['id','cart','menu_item','deal','quantity']

@admin.register(Order)
class  OrderAdmin(admin.ModelAdmin):
    list_display = ['id','user','restaurant','payment','total_price','current_status','delivery_address']

@admin.register(OrderItem)
class  OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id','order','menu_item','deal','quantity', 'price_at_order']

@admin.register(OrderStatusHistory)
class  OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['id','order','status','changed_by','timestamp']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id','user','total_amount','payment_status','payment_method','transaction_id']
