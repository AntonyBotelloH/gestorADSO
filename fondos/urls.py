from django.urls import path
from . import views

urlpatterns = [
    # Dashboard principal de fondos (Caja, Cartera, Formulario de registro)
    path('', views.dashboard_fondos, name='inicio_fondos'),
    
    # Catálogo de Conceptos y Tarifas
    path('conceptos/', views.listar_conceptos, name='conceptos'),
    
    # Configuración de Metas Financieras
    path('metas/', views.configurar_metas, name='metas'),
    
    # Detalle / Comprobante en PDF o vista web de un movimiento específico
    path('recibo/<int:movimiento_id>/', views.ver_recibo, name='ver_recibo'),
]