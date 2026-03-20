# planeacion/admin.py
from django.contrib import admin
from .models import Competencia, ResultadoAprendizaje, ActividadPlaneacion

@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'duracion_horas')
    search_fields = ('codigo', 'nombre')

@admin.register(ResultadoAprendizaje)
class RAPAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'competencia')
    list_filter = ('competencia',)
    search_fields = ('descripcion', 'competencia__codigo', 'competencia__nombre')

@admin.register(ActividadPlaneacion)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('ficha', 'fase', 'estado', 'instructor', 'fecha_inicio', 'fecha_fin', 'duracion_dias')
    list_filter = ('ficha', 'fase', 'estado', 'instructor')
    search_fields = ('ficha__codigo_ficha', 'fase', 'actividad_proyecto', 'instructor__first_name', 'instructor__last_name')
    raw_id_fields = ('ficha', 'instructor')
    filter_horizontal = ('raps',)
    autocomplete_fields = ('raps',)

    def duracion_dias(self, obj):
        if obj.fecha_fin and obj.fecha_inicio:
            return (obj.fecha_fin - obj.fecha_inicio).days
        return None
    duracion_dias.short_description = 'Duración (días)'
