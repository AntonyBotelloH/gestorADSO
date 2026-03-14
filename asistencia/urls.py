from django.urls import path
from . import views

urlpatterns = [
    # Toma de asistencia diaria (o edición de una sesión específica)
    path('', views.inicio_asistencia, name='inicio_asistencia'),
    
    # Tabla de días anteriores y filtros por fecha
    path('historial/', views.historial_asistencias, name='historial_asistencia'),
    
    # Dashboard de rendimiento, retardos y riesgo de deserción
    path('estadisticas/', views.estadisticas_asistencia, name='estadisticas_asistencia'),
]