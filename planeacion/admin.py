# planeacion/admin.py
from django.contrib import admin
from .models import Competencia, ResultadoAprendizaje, FaseProyecto, ActividadPlaneacion

@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'duracion_horas')
    search_fields = ('codigo', 'nombre')

@admin.register(ResultadoAprendizaje)
class RAPAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'competencia')
    list_filter = ('competencia',)

@admin.register(ActividadPlaneacion)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('ficha', 'fase', 'estado', 'fecha_inicio', 'fecha_fin')
    list_filter = ('ficha', 'fase', 'estado')