from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from collections import defaultdict
from order.models import Cart, CartItem, Order, OrderItem, OrderStatusHistory, Payment
from restaurants.models import Restaurants
from user.models import User
from restaurants.models import MenuItem, Deal
from order.serializer import CartSerializer, CartItemSerializer,OrderSerializer, CheckoutSerializer
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# ─── Cart ────────────────────────

class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            serializer = CartSerializer(cart)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddToCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['menu_item_id','deal_id'],
            properties={
                'menu_item_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the menu item to add'),
                'deal_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the deal to add'),
            }
        ),
        responses={200: CartSerializer}
    )
    def post(self, request):
        try:
            cart, _ = Cart.objects.get_or_create(user=request.user)

            menu_item_id = request.data.get("menu_item_id")
            deal_id = request.data.get("deal_id")

            if not menu_item_id and not deal_id:
                return Response(
                    {"error": "Provide either menu_item_id or deal_id."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if menu_item_id:
                try:
                    menu_item = MenuItem.objects.get(id=menu_item_id, is_available=True)
                except MenuItem.DoesNotExist:
                    return Response({"error": "Menu item not found or unavailable."}, status=status.HTTP_404_NOT_FOUND)

                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart, menu_item=menu_item, defaults={"quantity": 1}
                )
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()

            if deal_id:
                try:
                    deal = Deal.objects.get(id=deal_id, is_active=True)
                except Deal.DoesNotExist:
                    return Response({"error": "Deal not found or inactive."}, status=status.HTTP_404_NOT_FOUND)

                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart, deal=deal, defaults={"quantity": 1}
                )
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()

            cart.refresh_from_db()
            return Response(
                {"message": "Added to cart", "data": CartSerializer(cart).data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateCartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['quantity'],
            properties={
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='New quantity (min 1)'),
            }
        ),
        responses={200: CartItemSerializer}
    )
    def patch(self, request, item_id):
        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            quantity = request.data.get("quantity")

            if not quantity or int(quantity) < 1:
                return Response({"error": "Quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)

            cart_item.quantity = int(quantity)
            cart_item.save()

            return Response(
                {"message": "Cart item updated", "data": CartItemSerializer(cart_item).data},
                status=status.HTTP_200_OK
            )
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RemoveCartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, item_id):
        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            cart_item.delete()
            return Response({"message": "Item removed from cart."}, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─── Checkout ────────────────────────────────────────────────────────────────

class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['delivery_address', 'payment_method'],
            properties={
                'delivery_address': openapi.Schema(type=openapi.TYPE_STRING, description='Delivery address'),
                'payment_method': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['cash', 'stripe', 'jazzcash', 'easypaisa'],
                    description='Payment method'
                ),
                'transaction_id': openapi.Schema(type=openapi.TYPE_STRING, description='Required for online payments'),
            }
        ),
        responses={201: openapi.Response('Checkout complete')}
    )
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        delivery_address = serializer.validated_data['delivery_address']
        payment_method = serializer.validated_data['payment_method']
        transaction_id = serializer.validated_data.get('transaction_id', '')

        try:
            cart = Cart.objects.prefetch_related(
                'items__menu_item__restaurant_id',
                'items__deal__restaurant_id'
            ).get(user=request.user)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

        if not cart.items.exists():
            return Response({"error": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Group cart items by restaurant
        restaurant_groups = defaultdict(list)
        for item in cart.items.all():
            if item.menu_item:
                restaurant = item.menu_item.restaurant_id
            else:
                restaurant = item.deal.restaurant_id
            restaurant_groups[restaurant].append(item)

        successful_orders = []
        failed_orders = []
        total_successful_amount = 0

        for restaurant, items in restaurant_groups.items():
            try:
                with transaction.atomic():
                    # Calculate total for this restaurant
                    order_total = sum(item.subtotal for item in items)

                    order = Order.objects.create(
                        user=request.user,
                        restaurant=restaurant,
                        total_price=order_total,
                        delivery_address=delivery_address,
                        current_status='pending'
                    )

                    # Create order items with frozen prices
                    for item in items:
                        OrderItem.objects.create(
                            order=order,
                            menu_item=item.menu_item if item.menu_item else None,
                            deal=item.deal if item.deal else None,
                            quantity=item.quantity,
                            price_at_order=item.menu_item.price if item.menu_item else item.deal.combo_price
                        )

                    # Create initial status history
                    OrderStatusHistory.objects.create(
                        order=order,
                        status='pending',
                        changed_by=request.user
                    )

                    total_successful_amount += order_total
                    successful_orders.append({
                        "restaurant": restaurant.name,
                        "order_id": order.id,
                        "total": order_total
                    })

            except Exception as e:
                failed_orders.append({
                    "restaurant": restaurant.name,
                    "reason": str(e)
                })

        if not successful_orders:
            return Response(
                {"error": "Checkout failed for all restaurants.", "failed_orders": failed_orders},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create one payment for all successful orders
        payment = Payment.objects.create(
            user=request.user,
            total_amount=total_successful_amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            payment_status='pending' if payment_method == 'cash' else 'success'
        )

        # Link payment to successful orders
        Order.objects.filter(
            id__in=[o['order_id'] for o in successful_orders]
        ).update(payment=payment)

        # Clear only items that were successfully ordered
        successful_restaurants = [o['restaurant'] for o in successful_orders]
        cart.items.filter(
            menu_item__restaurant_id__name__in=successful_restaurants
        ).delete()
        cart.items.filter(
            deal__restaurant_id__name__in=successful_restaurants
        ).delete()

        return Response({
            "message": "Checkout complete.",
            "successful_orders": successful_orders,
            "failed_orders": failed_orders,
            "payment": {
                "id": payment.id,
                "total_amount": total_successful_amount,
                "payment_method": payment_method,
                "payment_status": payment.payment_status
            }
        }, status=status.HTTP_201_CREATED)


# ─── Orders ──────────────────────────────────────────────────────────────────

class UserOrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            orders = Order.objects.filter(user=request.user).select_related(
                'restaurant', 'payment'
            ).prefetch_related('items__menu_item', 'items__deal', 'status_history')

            serializer = OrderSerializer(orders, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserOrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.select_related(
                'restaurant', 'payment'
            ).prefetch_related(
                'items__menu_item__restaurant_id', 'items__deal__restaurant_id', 'status_history__changed_by'
            ).get(id=order_id, user=request.user)

            serializer = OrderSerializer(order)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)

            if order.current_status != 'pending':
                return Response(
                    {"error": "Order can only be cancelled when status is pending."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            order.current_status = 'cancelled'
            order.save()

            OrderStatusHistory.objects.create(
                order=order,
                status='cancelled',
                changed_by=request.user
            )

            return Response({"message": "Order cancelled successfully."}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─── Admin ───────────────────────────────────────────────────────────────────

class AdminOrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get(self, request):
        try:
            orders = Order.objects.select_related(
                'user', 'restaurant', 'payment'
            ).prefetch_related('items__menu_item__restaurant_id', 'items__deal__restaurant_id', 'status_history__changed_by')

            serializer = OrderSerializer(orders, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminUpdateOrderStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['status'],
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['pending', 'accepted', 'preparing', 'out_for_delivery', 'delivered', 'cancelled'],
                    description='New order status'
                ),
            }
        ),
        responses={200: OrderSerializer}
    )
    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            new_status = request.data.get("status")

            if not new_status:
                return Response({"error": "Status is required."}, status=status.HTTP_400_BAD_REQUEST)

            if new_status not in dict(Order.CHOICE_FIELDS_ORDER_STATUS).keys():
                return Response(
                    {"error": f"Invalid status. Choices are: {list(dict(Order.CHOICE_FIELDS_ORDER_STATUS).keys())}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            order.current_status = new_status
            order.save()

            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                changed_by=request.user
            )
            if new_status == 'delivered':
                if order.payment and order.payment.payment_method == 'cash':
                    order.payment.payment_status = 'success'
                    order.payment.save()

            return Response(
                {"message": "Order status updated.", "data": OrderSerializer(order).data},
                status=status.HTTP_200_OK
            )
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

#-----------Report-------------------------------------------------

class AdminOverviewView(APIView):
    """
    Top level dashboard cards:
    total orders, total revenue, active restaurants, total users.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
 
    def get(self, request):
        try:
            total_orders = Order.objects.count()
 
            total_revenue = Order.objects.filter(
                current_status='delivered'
            ).aggregate(
                total=Sum('total_price')
            )['total'] or 0
 
            active_restaurants = Restaurants.objects.filter(is_active=True).count()
 
            total_users = User.objects.filter(is_admin=False).count()
 
            return Response({
                "data": {
                    "total_orders": total_orders,
                    "total_revenue": total_revenue,
                    "active_restaurants": active_restaurants,
                    "total_users": total_users,
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
 
class AdminPopularItemsView(APIView):
    """
    Top N menu items by total quantity sold.
    GET /admin/analytics/popular-items/?limit=10
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
 
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
 
            popular_items = OrderItem.objects.filter(
                menu_item__isnull=False,
                order__current_status='delivered'
            ).values(
                'menu_item__id',
                'menu_item__name',
                'menu_item__price',
                'menu_item__restaurant_id__name'
            ).annotate(
                total_sold=Sum('quantity'),
                total_revenue=Sum(F('quantity') * F('price_at_order'))
            ).order_by('-total_sold')[:limit]
 
            return Response({"data": list(popular_items)}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
 
class AdminPopularDealsView(APIView):
    """
    Top N deals by total quantity sold.
    GET /admin/analytics/popular-deals/?limit=10
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
 
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
 
            popular_deals = OrderItem.objects.filter(
                deal__isnull=False,
                order__current_status='delivered'
            ).values(
                'deal__id',
                'deal__name',
                'deal__combo_price',
                'deal__restaurant_id__name'
            ).annotate(
                total_sold=Sum('quantity'),
                total_revenue=Sum(F('quantity') * F('price_at_order'))
            ).order_by('-total_sold')[:limit]
 
            return Response({"data": list(popular_deals)}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
 
class AdminRevenueByRestaurantView(APIView):
    """
    Total revenue and order count per restaurant.
    Only counts delivered orders.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
 
    def get(self, request):
        try:
            revenue = Order.objects.filter(
                current_status='delivered'
            ).values(
                'restaurant__id',
                'restaurant__name',
            ).annotate(
                total_revenue=Sum('total_price'),
                total_orders=Count('id')
            ).order_by('-total_revenue')
 
            return Response({"data": list(revenue)}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
 
class AdminOrdersByStatusView(APIView):
    """
    Count of orders grouped by current status.
    Useful for dashboard status breakdown cards.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
 
    def get(self, request):
        try:
            breakdown = Order.objects.values(
                'current_status'
            ).annotate(
                count=Count('id')
            ).order_by('current_status')
 
            return Response({"data": list(breakdown)}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
 
class AdminRevenueOverTimeView(APIView):
    """
    Revenue trend over time, filterable by range.
    GET /admin/analytics/revenue-over-time/?range=daily|weekly|monthly
    Only counts delivered orders.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
 
    def get(self, request):
        try:
            range_filter = request.query_params.get('range', 'daily')
 
            trunc_map = {
                'daily': TruncDate,
                'weekly': TruncWeek,
                'monthly': TruncMonth,
            }
 
            if range_filter not in trunc_map:
                return Response(
                    {"error": "Invalid range. Choose from: daily, weekly, monthly."},
                    status=status.HTTP_400_BAD_REQUEST
                )
 
            TruncFunc = trunc_map[range_filter]
 
            revenue_trend = Order.objects.filter(
                current_status='delivered'
            ).annotate(
                period=TruncFunc('created_at')
            ).values('period').annotate(
                total_revenue=Sum('total_price'),
                total_orders=Count('id')
            ).order_by('period')
 
            return Response({
                "range": range_filter,
                "data": list(revenue_trend)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 