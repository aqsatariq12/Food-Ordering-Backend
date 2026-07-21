from rest_framework import serializers
from order.models import Payment, Cart, CartItem, Order, OrderItem, OrderStatusHistory


class CartItemSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    restaurant = serializers.SerializerMethodField()
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id','name','price','image','type','restaurant','quantity','subtotal']

    def get_name(self, obj):
        return obj.menu_item.name if obj.menu_item else obj.deal.name

    def get_price(self, obj):
        return obj.menu_item.price if obj.menu_item else obj.deal.combo_price

    def get_image(self, obj):
        item = obj.menu_item or obj.deal
        return item.image.url if item.image else None

    def get_type(self, obj):
        return "menu_item" if obj.menu_item else "deal"
    
    def get_restaurant(self,obj):
        return obj.menu_item.restaurant_id.name if obj.menu_item else obj.deal.restaurant_id.name



class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only = True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id','items','total_price','updated_at']
    

class OrderItemSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    # price = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    # restaurant = serializers.SerializerMethodField()
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ['id', 'name', 'image', 'type', 'quantity', 'price_at_order', 'subtotal']

    def get_name(self, obj):
        if obj.menu_item:
            return obj.menu_item.name
        return obj.deal.name if obj.deal else None

    # def get_price(self, obj):
    #     if obj.menu_item:
    #         return obj.menu_item.price
    #     return obj.deal.combo_price if obj.deal else None

    def get_image(self, obj):
        item = obj.menu_item or obj.deal
        return item.image.url if item and item.image else None

    def get_type(self, obj):
        return "menu_item" if obj.menu_item else "deal"

    # def get_restaurant(self, obj):
    #     if obj.menu_item:
    #         return obj.menu_item.restaurant_id.name
    #     return obj.deal.restaurant_id.name if obj.deal else None
    
class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.SerializerMethodField()

    class Meta:
        model = OrderStatusHistory
        fields = ['id','status','changed_by','timestamp']
    
    def get_changed_by(self, obj):
        if obj.changed_by:
            return {
                'id':obj.changed_by.id,
                'username': obj.changed_by.username,
                'email':obj.changed_by.email,
            } 
        return None
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "payment_method",
            "payment_status",
            "total_amount",
        ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only = True)
    status_history = OrderStatusHistorySerializer(many=True, read_only = True)
    order_id = serializers.SerializerMethodField()
    payment = PaymentSerializer(read_only=True)
    restaurant = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['order_id', 'restaurant', 'items', 'total_price', 'current_status', 'payment',
                  'delivery_address', 'status_history', 'created_at', 'updated_at']
    
    def get_order_id(self,obj):
        return obj.id
    
    def get_restaurant(self, obj):
        if obj.restaurant:
            return {
                'id':obj.restaurant.id,
                'name':obj.restaurant.name,
            }
        
class CheckoutSerializer(serializers.Serializer):
    delivery_address = serializers.CharField(max_length = 255)
    payment_method = serializers.ChoiceField(choices=Payment.CHOICE_FIELDS_PAY_METHOD)
    transaction_id = serializers.CharField(required=False, allow_blank = True)

    def validate(self, attrs):
        if attrs['payment_method'] != 'cash' and not attrs.get('transaction_id'):
            raise serializers.ValidationError(
                {"transaction_id": "Transaction ID is required for online payments."}
            )
        return attrs