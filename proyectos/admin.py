from django.contrib import admin
from .models import Proyecto, Tarea, DailyScrum, RevisionTecnica, Sprint

# Configuración para ver tareas dentro del proyecto
class TareaInline(admin.TabularInline):
    model = Tarea
    extra = 1
    # Agregamos 'sprint' para que puedas asignarlo rápido desde el proyecto
    fields = ('nombre', 'sprint', 'responsable', 'estado', 'prioridad')

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ficha', 'scrum_master', 'estado', 'fecha_inicio')
    list_filter = ('ficha', 'estado', 'fecha_inicio')
    search_fields = ('nombre', 'scrum_master__first_name', 'scrum_master__last_name', 'ficha__codigo_ficha')
    inlines = [TareaInline]
    list_editable = ('estado',) # Permite cambiar el estado rápido desde la lista

# ¡NUEVO! Panel de administración para los Sprints
@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'proyecto', 'fecha_inicio', 'fecha_fin', 'estado')
    list_filter = ('estado', 'proyecto')
    search_fields = ('nombre', 'proyecto__nombre')
    list_editable = ('estado',) # Permite activar o completar sprints rápidamente
    date_hierarchy = 'fecha_inicio'

@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    # Agregamos 'sprint' a la vista
    list_display = ('nombre', 'proyecto', 'sprint', 'responsable', 'estado', 'prioridad', 'fecha_limite')
    list_filter = ('estado', 'prioridad', 'sprint', 'proyecto__ficha')
    search_fields = ('nombre', 'responsable__first_name', 'proyecto__nombre')
    list_editable = ('estado', 'prioridad')

@admin.register(DailyScrum)
class DailyScrumAdmin(admin.ModelAdmin):
    # Agregamos 'sprint' para saber en qué iteración se hizo el daily
    list_display = ('proyecto', 'sprint', 'fecha', 'aprendiz_reportado')
    list_filter = ('fecha', 'proyecto__ficha')
    readonly_fields = ('fecha',) # La fecha se pone sola, mejor no tocarla
    search_fields = ('proyecto__nombre', 'logros', 'planes')

@admin.register(RevisionTecnica)
class RevisionTecnicaAdmin(admin.ModelAdmin):
    # Cambiamos 'hito' por 'sprint_evaluado'
    list_display = ('proyecto', 'sprint_evaluado', 'instructor', 'estado_resultado', 'fecha')
    list_filter = ('estado_resultado', 'fecha', 'proyecto__ficha')
    # Actualizamos la búsqueda para que busque por el nombre del sprint
    search_fields = ('proyecto__nombre', 'sprint_evaluado__nombre', 'observaciones')
    list_editable = ('estado_resultado',)