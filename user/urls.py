from django.urls import path
from user.views import RegisterAPIView,LoginAPIView
urlpatterns = [
   path('register/',RegisterAPIView.as_view(), name = 'signup'),
   path('login/',LoginAPIView.as_view(), name = 'signin'),
]