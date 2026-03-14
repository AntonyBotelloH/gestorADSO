# planeacion/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Ruta principal del módulo (Fases y Actividades)
    path('', views.inicio_planeacion, name='inicio_planeacion'),
    
    # Ruta para los Resultados de Aprendizaje
    path('raps/', views.listar_raps, name='listar_raps'),
    
    # Ruta para las Competencias
    path('competencias/', views.listar_competencias, name='listar_competencias'),
]