from django.contrib import admin
from .models import Concepto, MetaFinanciera, Movimiento

@admin.register(Concepto)
class ConceptoAdmin(admin.ModelAdmin):
    # Columnas que se verán en la tabla principal
    list_display = ('nombre', 'categoria', 'tipo_operacion', 'valor_sugerido', 'vigente_desde', 'activo')
    # Filtros laterales mágicos
    list_filter = ('activo', 'categoria', 'tipo_operacion')
    # Barra de búsqueda
    search_fields = ('nombre',)
    # Campos editables directamente desde la tabla (para hacer cambios rápidos)
    list_editable = ('valor_sugerido', 'activo')

@admin.register(MetaFinanciera)
class MetaFinancieraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ficha', 'valor_objetivo', 'fecha_limite', 'activa')
    list_filter = ('activa', 'ficha')
    search_fields = ('nombre', 'ficha__codigo_ficha', 'descripcion')
    list_editable = ('activa',)
    # Ordenar por fecha límite para ver las más urgentes primero
    ordering = ('fecha_limite',)

@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    # Usamos id para mostrar el "Número de comprobante"
    list_display = ('id', 'ficha', 'concepto', 'responsable', 'valor', 'fecha', 'estado')
    list_filter = ('estado', 'concepto__tipo_operacion', 'ficha', 'fecha')
    # Permite buscar por el nombre del aprendiz, número de ficha o concepto
    search_fields = ('responsable__first_name', 'responsable__last_name', 'responsable__documento', 'ficha__codigo_ficha', 'concepto__nombre')
    # Campo de fecha de solo lectura (ya que auto_now_add=True lo maneja automático)
    readonly_fields = ('fecha',)
    list_editable = ('estado',)