from django.contrib import admin
from .models import SesionClase, RegistroAsistencia

@admin.register(SesionClase)
class SesionClaseAdmin(admin.ModelAdmin):
    # Columnas que verás en la tabla principal
    list_display = ('fecha', 'ficha', 'tema_tratado')
    # Filtros laterales
    list_filter = ('fecha', 'ficha')
    # Barra de búsqueda
    search_fields = ('tema_tratado', 'ficha__codigo_ficha')
    # Navegación por fechas en la parte superior
    date_hierarchy = 'fecha'

@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('aprendiz', 'sesion', 'estado')
    list_filter = ('estado', 'sesion__fecha', 'sesion__ficha')
    # Permite buscar por el nombre o apellido del aprendiz
    search_fields = ('aprendiz__first_name', 'aprendiz__last_name')