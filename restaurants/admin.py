from django.contrib import admin
from restaurants.models import Restaurants, Category, MenuItem,Deal, DealItem
# Register your models here.

@admin.register(Category)
class  CategoryAdmin(admin.ModelAdmin):
    list_display = ['id','name','slug','created_by','created_at','updated_at']

@admin.register(Restaurants)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['id','name','description','address','image','is_featured','is_active','created_by','created_at','updated_at']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['id','name','description','price','image','is_available','is_featured','created_by','restaurant_id','category_id','created_at','updated_at']


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display =['id','name','description','combo_price','image','is_active','is_featured','restaurant_id','created_by','created_at','updated_at']

@admin.register(DealItem)
class DealItemAdmin(admin.ModelAdmin):
    list_display = ['id','deal_id','quantity']