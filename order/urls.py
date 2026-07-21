from django.urls import path
from .views import CartView, AddToCartView, UpdateCartItemView, RemoveCartItemView,CheckoutView,UserOrderListView, UserOrderDetailView,CancelOrderView,AdminOrderListView,AdminOrdersByStatusView,AdminOverviewView,AdminPopularDealsView,AdminPopularItemsView,AdminRevenueByRestaurantView,AdminRevenueOverTimeView,AdminUpdateOrderStatusView
urlpatterns = [
    
    #-------------cart
    path('cart/',CartView.as_view(), name='get-cart'),
    path('cart/add/',AddToCartView.as_view(), name='addtocart'),
    path('cart/update-item/<int:item_id>/',UpdateCartItemView.as_view(),name='updatecartitem'),
    path('cart/delete-item/<int:item_id>/',RemoveCartItemView.as_view(), name='removecartitem'),

    #---------Check Out
    path('checkout/',CheckoutView.as_view(), name='checkout'),

    #------ orders

    path('orders/',UserOrderListView.as_view(), name="orderlist"),
    path('order/<int:order_id>',UserOrderDetailView.as_view(), name = 'orderdetail'),
    path('order/<int:order_id>/cancel/', CancelOrderView.as_view(), name = 'cancelorder'),

    #--------admin order 
    path('admin/orders',AdminOrderListView.as_view(), name='all-orders'),
    path('admin/orders/<int:order_id>/status/',AdminUpdateOrderStatusView.as_view(), name='order-statuschanged'),

    #------admin analytics
    path('admin/analytics/overview/',AdminOverviewView.as_view(), name = 'overview'),
    path('admin/analytics/popular-items/',AdminPopularItemsView.as_view(), name = 'popular-items'),
    path('admin/analytics/popular-deals/',AdminPopularDealsView.as_view(), name = 'popular-deal'),
    path('admin/analytics/revenue-by-restaurant/',AdminRevenueByRestaurantView.as_view(), name = 'revenue-by-restaurant'),
    path('admin/analytics/revenue-over-time/',AdminRevenueOverTimeView.as_view(), name = 'revenue-over-time'),
    path('admin/analytics/orders-by-status/', AdminOrdersByStatusView.as_view(), name = 'order-by-status'),

]