from django.contrib import admin
from django.urls import path

from usuarios.views import *

urlpatterns = [
    path('usuario/', inicio_usuario, name='inicio_usuario'),
    path('usuario/crear/', crear_usuario, name='crear_usuario'),
    path('usuario/editar/<int:pk>/', editar_usuario, name='editar_usuario'),
    
    path('ficha/', inicio_ficha, name='inicio_ficha'),
    path('fichas/crear/', crear_ficha, name='crear_ficha'),
    path('fichas/listar/', listar_fichas, name='listar_fichas'),
    path('fichas/cambiar/', set_ficha_activa, name='cambiar_ficha'),
    path('fichas/editar/<str:codigo_ficha>/', editar_ficha, name='editar_ficha'),
]