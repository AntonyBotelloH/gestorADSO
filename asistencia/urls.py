from django.contrib import admin
from django.urls import path

from asistencia.views import *

urlpatterns = [
    path('', inicio_asistencia, name='inicio_asistencia'),
]
