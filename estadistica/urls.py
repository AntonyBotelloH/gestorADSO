from django.urls import path
from . import views


urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_sena, name='dashboard_estadistica'),
    
    # Rutas para Informes
    path('informes/', views.informe_list, name='informe_list'),
    path('informes/nuevo/', views.informe_create, name='informe_create'),
    
    # Rutas para Liquidaciones
    path('liquidaciones/', views.liquidacion_list, name='liquidacion_list'),
    path('liquidaciones/nueva/', views.liquidacion_create, name='liquidacion_create'),
]