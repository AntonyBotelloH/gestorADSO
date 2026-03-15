from django.urls import path
from asistencia.views import inicio_asistencia, historial_asistencias, estadisticas_asistencia

urlpatterns = [
    # Toma de asistencia diaria (o edición de una sesión específica)
    path('', inicio_asistencia, name='inicio_asistencia'),
    
    # Tabla de días anteriores y filtros por fecha
    path('historial/', historial_asistencias, name='historial_asistencia'),
    
    # Dashboard de rendimiento, retardos y riesgo de deserción
    path('estadisticas/', estadisticas_asistencia, name='estadisticas_asistencia'),
]