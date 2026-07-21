from rest_framework import serializers
from restaurants.models import Category,MenuItem,Restaurants,Deal,DealItem

class AllRestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurants
        fields = ['id','name','image','created_by','created_at']
        
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name','slug','created_at','updated_at']
        extra_kwargs = {
            'name':{'required':True}
        }

class AllCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name','created_by','created_at']
 
class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(source="category_id", read_only=True)
    restaurant = AllRestaurantSerializer(source="restaurant_id", read_only=True)
    class Meta:
        model = MenuItem
        fields = ['id','restaurant_id','category_id','name','description','price','image','is_available','is_featured','restaurant','category','created_at','updated_at',]
        extra_kwargs ={
            'name':{'required':True},
            'price':{'required':True},
            'restaurant_id':{'required':True},
            'category_id':{'required':True}
        }

class SearchMenuItemSerializer(serializers.ModelSerializer):
    restaurant = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'price', 'image', 'restaurant', 'category']

    def get_restaurant(self, obj):
        return {"id": obj.restaurant_id.id, "name": obj.restaurant_id.name}

    def get_category(self, obj):
        if obj.category_id:
            return {"id": obj.category_id.id, "name": obj.category_id.name}
        return None


class SearchCategorySerializer(serializers.ModelSerializer):
    restaurants = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'restaurants']

    def get_restaurants(self, obj):
        restaurants = Restaurants.objects.filter(
            menu_items__category_id=obj
        ).prefetch_related('menu_items').distinct()
        return [
            {
                "id": r.id,
                "name": r.name,
                "menu_items": [
                    {"id": m.id, "name": m.name}
                    for m in r.menu_items.filter(category_id=obj)
                ]
            }
            for r in restaurants
        ]


class SearchRestaurantSerializer(serializers.ModelSerializer):
    menu_items = serializers.SerializerMethodField()

    class Meta:
        model = Restaurants
        fields = ['id', 'name', 'image', 'menu_items']

    def get_menu_items(self, obj):
        return [
            {
                "id": m.id,
                "name": m.name,
                "category": {"id": m.category_id.id, "name": m.category_id.name} if m.category_id else None
            }
            for m in obj.menu_items.filter(is_available=True).select_related('category_id')
        ]


class AllMenuItemSerializer(serializers.ModelSerializer):
    restaurant = AllRestaurantSerializer(source = "restaurant_id",read_only=True)
    category = AllCategorySerializer(source="category_id", read_only=True)
    class Meta:
        model = MenuItem
        fields = ['id','name','description','price','image','restaurant','category']

class RestaurantMenuItemSerializer(serializers.ModelSerializer):
    category = AllCategorySerializer(source="category_id", read_only=True)
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'price', 'image', 'category']

class RestaurantSerializer(serializers.ModelSerializer):
    menu_items = RestaurantMenuItemSerializer(many=True, read_only = True)
    class Meta:
        model = Restaurants
        fields = ['id','name','description','address','image','is_featured','is_active','menu_items','created_at','updated_at',]
        extra_kwargs ={
            'name':{'required':True}
        }






class DealItemSerializer(serializers.ModelSerializer):
    menu_item = AllMenuItemSerializer(source = 'menu_item_id', read_only=True)
    class Meta:
        model = DealItem
        fields = ['id','deal_id','quantity',"menu_item_id",'menu_item',]
        extra_kwargs = {
            "deal_id": {"required": True},
            "menu_item_id": {"required": True},
            "quantity": {"required": True},
        }
    

class DealSerializer(serializers.ModelSerializer):
    items = DealItemSerializer(source = 'deal_item',many=True,read_only=True)
    class Meta:
        model = Deal
        fields = ['id','restaurant_id','name','description','combo_price','image','is_active','is_featured','created_by','created_at','updated_at','items']
        extra_kwargs ={
            'name':{'required':True},
            'combo_price':{'required':True},
            'restaurant_id': {'required': True},
        }