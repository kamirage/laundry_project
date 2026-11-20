from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/new/', views.create_order, name='create_order'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('staff/orders/<int:pk>/inspection/', views.staff_inspection, name='staff_inspection'),
    path('profile/', views.profile, name='profile'),
    path('about/', views.about, name='about'),
    path('search/', views.search, name='search'),
    path('api/services/', views.search_json, name='search_json'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='laundry/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
