from django.urls import path
from . import views


urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_sena, name='dashboard_estadistica'),
    
    # Rutas para Contratos
    path('contratos/', views.contrato_list, name='contrato_list'),
    path('contratos/nuevo/', views.contrato_create, name='contrato_create'),
    path('contratos/editar/<int:pk>/', views.contrato_update, name='contrato_update'),
    path('contratos/eliminar/<int:pk>/', views.contrato_delete, name='contrato_delete'),

    # Rutas para Obligaciones
    path('obligaciones/', views.obligacion_list, name='obligacion_list'),
    path('obligaciones/nueva/', views.obligacion_create, name='obligacion_create'),
    path('obligaciones/editar/<int:pk>/', views.obligacion_update, name='obligacion_update'),
    path('obligaciones/eliminar/<int:pk>/', views.obligacion_delete, name='obligacion_delete'),

    # Rutas para Informes
    path('informes/', views.informe_list, name='informe_list'),
    path('informes/nuevo/', views.informe_create, name='informe_create'),
    
    # Rutas para Liquidaciones
    path('liquidaciones/', views.liquidacion_list, name='liquidacion_list'),
    path('liquidaciones/nueva/', views.liquidacion_create, name='liquidacion_create'),
]