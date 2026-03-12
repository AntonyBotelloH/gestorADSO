from django.contrib import admin
from django.urls import path

from usuarios.views import *

urlpatterns = [
    path('', inicio_usuario, name='inicio_usuario'),
    
    path('nuevo/', crear_usuario, name='crear_aprendiz'),
    path('editar/<int:pk>/', editar_usuario, name='editar_usuario'),
    
    path('fichas/nuevo/', crear_ficha, name='crear_ficha'),
]
