from django.contrib import admin
from django.urls import path

from fondos.views import *

urlpatterns = [
    path('', inicio_fondo, name='inicio_fondos'),
]
