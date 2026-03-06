from django.contrib import admin
from django.urls import path

from proyectos.views import *

urlpatterns = [
    path('', inicio_proyecto, name='inicio_proyecto'),
]
