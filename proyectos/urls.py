from django.urls import path
from . import views

urlpatterns = [
    # Listado principal de proyectos de la ficha activa
    # URL: /proyectos/
    path('', views.listar_proyectos, name='proyectos'),

    # Formulario para crear un equipo y asignar integrantes
    # URL: /proyectos/nuevo/
    path('nuevo/', views.nuevo_grupo, name='nuevo_grupo'),

    # Ficha técnica y bitácora de un proyecto específico
    # URL: /proyectos/5/
    path('<int:proyecto_id>/', views.detalles_proyecto, name='detalles_proyecto'),

    # Tablero Kanban (To Do, In Progress, Done)
    # URL: /proyectos/5/tablero/
    path('<int:proyecto_id>/tablero/', views.tablero_kanban, name='tablero_kanban'),

    # Registro de reporte diario por el Scrum Master
    # URL: /proyectos/5/daily/
    path('<int:proyecto_id>/daily/', views.registrar_daily, name='registrar_daily'),

    # Evaluación de avance técnico realizada por el Instructor
    # URL: /proyectos/5/avance/
    path('<int:proyecto_id>/avance/', views.registrar_avance, name='registrar_avance'),
]