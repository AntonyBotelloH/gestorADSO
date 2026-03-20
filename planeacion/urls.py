# planeacion/urls.py
from django.urls import path
from planeacion.views import *

urlpatterns = [
    
    # Ruta principal del módulo (Fases y Actividades)
    path('', inicio_planeacion, name='inicio_planeacion'),
    
    # Rutas para el CRUD de Actividades de Planeación
    path('actividad/nueva/', crear_actividad, name='crear_actividad'),
    path('actividad/editar/<int:pk>/', editar_actividad, name='editar_actividad'),
    path('actividad/<int:pk>/', detalle_actividad, name='detalle_actividad'),
    
    # Rutas para los Resultados de Aprendizaje
    path('raps/', listar_raps, name='listar_raps'), # Asegúrate que coincida con tus templates
    path('raps/nuevo/', crear_rap, name='crear_rap'),
    path('raps/editar/<int:pk>/', editar_rap, name='editar_rap'),
    path('raps/eliminar/<int:pk>/', eliminar_rap, name='eliminar_rap'),
    
    # Rutas para las Competencias
    path('competencias/', listar_competencias, name='listar_competencias'),
    path('competencias/nuevo/', crear_competencia, name='crear_competencia'),
    path('competencias/editar/<int:pk>/', editar_competencia, name='editar_competencia'),
    path('competencias/eliminar/<int:pk>/', eliminar_competencia, name='eliminar_competencia'),
    path('importar/', importar_curriculo, name='importar_curriculo'),

    # Ruta para exportar a Excel
    path('exportar/', exportar_planeacion_excel, name='exportar_planeacion'),

]