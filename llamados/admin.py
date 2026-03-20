from django.contrib import admin
from .models import EstrategiaPedagogica, FaltaReglamento, LlamadoAtencion, PlanMejoramiento

@admin.register(FaltaReglamento)
class FaltaReglamentoAdmin(admin.ModelAdmin):
    list_display = ('capitulo', 'gravedad', 'tipo_falta', 'descripcion_corta')
    list_filter = ('gravedad', 'tipo_falta')
    search_fields = ('capitulo', 'descripcion')
    ordering = ('capitulo',)

    def descripcion_corta(self, obj):
        return f"{obj.descripcion[:75]}..." if len(obj.descripcion) > 75 else obj.descripcion
    descripcion_corta.short_description = 'Descripción'

@admin.register(LlamadoAtencion)
class LlamadoAtencionAdmin(admin.ModelAdmin):
    list_display = ('aprendiz', 'ficha', 'instancia', 'falta_cometida', 'fecha_registro')
    list_filter = ('instancia', 'tipo_falta', 'gravedad', 'fecha_registro')
    search_fields = ('aprendiz__first_name', 'aprendiz__last_name', 'aprendiz__numero_documento', 'ficha__codigo_ficha')
    autocomplete_fields = ('aprendiz', 'ficha', 'falta_cometida')
    date_hierarchy = 'fecha_registro'

@admin.register(PlanMejoramiento)
class PlanMejoramientoAdmin(admin.ModelAdmin):
    list_display = ('llamado', 'estado', 'fecha_inicio', 'fecha_fin')
    list_filter = ('estado', 'fecha_inicio', 'fecha_fin')
    search_fields = ('llamado__aprendiz__first_name', 'llamado__aprendiz__last_name')
    filter_horizontal = ('estrategias',) # Hace que el selector múltiple se vea como dos cajas

@admin.register(EstrategiaPedagogica)
class EstrategiaPedagogicaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'plazo_dias')
    search_fields = ('nombre',)