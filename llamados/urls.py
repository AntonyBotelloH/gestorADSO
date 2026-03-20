from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_llamados, name='listar_llamados'),
    path('detalle/<int:pk>/', views.detalle_llamado, name='detalle_llamado'),
    path('detalle/<int:llamado_id>/crear-plan/', views.crear_plan, name='crear_plan'),
    path('plan/<int:plan_id>/editar/', views.editar_plan, name='editar_plan'),
    
    path('estrategias/', views.estrategias, name='estrategias'),
    path('estrategias/editar/<int:pk>/', views.editar_estrategia, name='editar_estrategia'),
    path('estrategias/eliminar/<int:pk>/', views.eliminar_estrategia, name='eliminar_estrategia'),
    
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('api/falta/<int:falta_id>/', views.api_detalle_falta, name='api_detalle_falta'),
    path('manual-convivencia/', views.catalogo_faltas, name='catalogo_faltas'),
]