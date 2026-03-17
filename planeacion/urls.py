# planeacion/urls.py
from django.urls import path
from planeacion.views import *

urlpatterns = [
    
    # Ruta principal del módulo (Fases y Actividades)
    path('', inicio_planeacion, name='inicio_planeacion'),
    
    # Rutas para el CRUD de Actividades de Planeación
    path('actividad/nueva/', crear_actividad, name='crear_actividad'),
    path('actividad/editar/<int:pk>/', editar_actividad, name='editar_actividad'),
    
    # Rutas para los Resultados de Aprendizaje
    path('raps/', listar_raps, name='listar_raps'), # Asegúrate que coincida con tus templates
    
    # Rutas para las Competencias
    path('competencias/', listar_competencias, name='listar_competencias'),
    path('importar/', importar_curriculo, name='importar_curriculo'),

]