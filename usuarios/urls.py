from django.contrib import admin
from django.urls import path

from usuarios.views import *

urlpatterns = [
    path('', inicio_usuario, name='inicio_usuario'),
]
