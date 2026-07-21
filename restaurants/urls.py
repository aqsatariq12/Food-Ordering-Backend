from django.urls import path
from restaurants.views import GetCategoryView, CreateCategoryView,GetAllCategoryView,UpdateCategoryView,DeleteCategoryView,CreateRestuarantView,GetAllRestaurantView,UpdateRestaurantView,GetRestaurantView,DeleteRestaurantView,CreateMenuItemView,GetAllMenuItemsView,GetMenuItemView,UpdateMenuItemView,DeleteMenuItemView,CreateDealView,GetAllDealView,GetDealView,UpdateDealView,DeleteDealView,CreateDealItemView,GetAllDealItemView,GetDealItemView,DeleteDealItemView,UpdateDealItemView,GlobalSearchView

urlpatterns = [
   #----- category 
   path('create-category/',CreateCategoryView.as_view(), name ='create-category'),
   path('category/<int:cat_id>',GetCategoryView.as_view(), name ='get-category'),
   path('all-category',GetAllCategoryView.as_view(), name = 'all-category'),
   path('update-category/<int:cat_id>/',UpdateCategoryView.as_view(), name = 'update-category'),
   path('delete-category/<int:cat_id>/',DeleteCategoryView.as_view(), name = 'delete-category'),

   #----- restaurants
   path('create-restaurant/',CreateRestuarantView.as_view(), name ='create-restaurant'),
   path('restaurant/<int:rest_id>',GetRestaurantView.as_view(), name ='get-restaurant'),
   path('all-restaurant',GetAllRestaurantView.as_view(), name = 'all-restaurant'),
   path('update-restaurant/<int:rest_id>/',UpdateRestaurantView.as_view(), name = 'update-restaurant'),
   path('delete-restaurant/<int:rest_id>/',DeleteRestaurantView.as_view(), name = 'delete-restaurant'),

   #--------- Menu items
   path('create-menuitem/',CreateMenuItemView.as_view(), name ='create-menuitem'),
   path('menuitem/<int:menu_id>',GetMenuItemView.as_view(), name ='get-menuitem'),
   path('all-menuitem',GetAllMenuItemsView.as_view(), name = 'all-menuitem'),
   path('update-menuitem/<int:menu_id>/',UpdateMenuItemView.as_view(), name = 'update-menuitem'),
   path('delete-menuitem/<int:menu_id>/',DeleteMenuItemView.as_view(), name = 'delete-menuitem'),

   #----------Deal
   path("create-deal/", CreateDealView.as_view(), name = 'create-deal'),
   path("deal/<int:deal_id>/", GetDealView.as_view(),name='get-deal'),
   path("all-deal/", GetAllDealView.as_view(), name = 'all-deal'),
   path("update-deal/<int:deal_id>/", UpdateDealView.as_view(), name = 'update-deal'),
   path("delete-deal/<int:deal_id>/", DeleteDealView.as_view(), name = 'delete-deal'),

   #----------Deal Item
   path("create-deal-item/", CreateDealItemView.as_view(),name='create-dealitem'),
   path("deal-item/<int:item_id>/", GetDealItemView.as_view(),name='get-dealitem'),
   path("all-deal-item/", GetAllDealItemView.as_view(), name='getall-dealitem'),
   path("update-deal-item/<int:item_id>/", UpdateDealItemView.as_view(),name='update-dealitem'),
   path("delete-deal-item/<int:item_id>/", DeleteDealItemView.as_view(), name='delete-dealitem'),

   #------Global Search by Category, Restaurant and Menu items

   path('search/', GlobalSearchView.as_view(), name='global search')

]