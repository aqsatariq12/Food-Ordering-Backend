from django.db import models
from django.utils.text import slugify
from user.models import User
# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100,null=True, blank=True, unique= True)
    slug = models.SlugField(max_length=100, null=True, blank=True, unique= True )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, related_name='created_category')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, related_name='updated_category')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Restaurants(models.Model):
    name = models.CharField(max_length=150,null= True, blank=True)
    description = models.TextField(null=True,blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to="restaurants/",blank=True, null= True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, related_name='created_restaurant')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,null=True,related_name='updated_restaurant')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
    
class MenuItem(models.Model):
    restaurant_id = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name="menu_items")
    category_id = models.ForeignKey(Category, models.SET_NULL, related_name= "menu_items", null=True, blank=True)
    name = models.CharField(max_length=150, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to="menu_items/",blank=True,null=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, related_name='created_menu')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,null=True,related_name='updated_menu')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.restaurant_id.name})"


class Deal(models.Model):
    restaurant_id = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name="deals")
    name =  models.CharField(max_length=150, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    combo_price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to="deals/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_deal')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,null=True,related_name='updated_deal')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering =['-created_at']
    
    def __str__(self):
        return f"{self.restaurant_id.name} ({self.name})"

class DealItem(models.Model):
    deal_id = models.ForeignKey(Deal,on_delete=models.CASCADE, related_name='deal_item')
    menu_item_id = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("deal_id","menu_item_id")
    
    def __str__(self):
        return f"{self.quantity} x {self.menu_item_id.name} in {self.deal_id.name}"