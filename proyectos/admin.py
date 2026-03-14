from django.contrib import admin
from .models import Proyecto, Tarea, DailyScrum, RevisionTecnica

# Configuración para ver tareas dentro del proyecto
class TareaInline(admin.TabularInline):
    model = Tarea
    extra = 1
    fields = ('nombre', 'responsable', 'estado', 'prioridad')

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ficha', 'scrum_master', 'estado', 'fecha_inicio')
    list_filter = ('ficha', 'estado', 'fecha_inicio')
    search_fields = ('nombre', 'scrum_master__first_name', 'scrum_master__last_name', 'ficha__codigo_ficha')
    inlines = [TareaInline]
    list_editable = ('estado',) # Permite cambiar el estado rápido desde la lista

@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'proyecto', 'responsable', 'estado', 'prioridad', 'fecha_limite')
    list_filter = ('estado', 'prioridad', 'proyecto__ficha')
    search_fields = ('nombre', 'responsable__first_name', 'proyecto__nombre')
    list_editable = ('estado', 'prioridad')

@admin.register(DailyScrum)
class DailyScrumAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'fecha', 'aprendiz_reportado')
    list_filter = ('fecha', 'proyecto__ficha')
    readonly_fields = ('fecha',) # La fecha se pone sola, mejor no tocarla
    search_fields = ('proyecto__nombre', 'logros', 'planes')

@admin.register(RevisionTecnica)
class RevisionTecnicaAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'hito', 'instructor', 'estado_resultado', 'fecha')
    list_filter = ('estado_resultado', 'fecha', 'proyecto__ficha')
    search_fields = ('proyecto__nombre', 'hito', 'observaciones')
    list_editable = ('estado_resultado',)