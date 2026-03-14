from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_llamados, name='listar_llamados'),
    path('detalle/', views.detalle_llamado, name='detalle_llamado'),
    path('estrategias/', views.estrategias, name='estrategias'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
]