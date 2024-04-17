from django.urls import path
from .views import calculate_distance
from distance_api import views

urlpatterns = [
    path('calculate_distance/', views.calculate_distance, name='calculate_distance'),
]
