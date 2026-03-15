from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_pendientes, name='listar_pendientes'),
]