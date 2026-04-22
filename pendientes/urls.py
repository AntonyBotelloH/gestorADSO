from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_pendientes, name='listar_pendientes'),
    # La URL para marcar/desmarcar una tarea como completada
    path('toggle/<int:pendiente_id>/', views.marcar_completada, name='marcar_completada'),
    # La URL para eliminar una tarea
    path('eliminar/<int:pendiente_id>/', views.eliminar_pendiente, name='eliminar_pendiente'),
    # La URL para limpiar todas las tareas que ya han sido completadas
    path('limpiar-completadas/', views.limpiar_completadas, name='limpiar_completadas'),
]
