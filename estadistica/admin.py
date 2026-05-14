from django.contrib import admin
from .models import Contrato, LiquidacionMensual, Obligacion, EvidenciaEsperada, InformeMensual, EjecucionObligacion, EvidenciaObligacion, Desplazamiento

@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ('numero_contrato', 'valor_total', 'fecha_inicio', 'fecha_fin')
    search_fields = ('numero_contrato',)

@admin.register(LiquidacionMensual)
class LiquidacionMensualAdmin(admin.ModelAdmin):
    list_display = ('numero_pago', 'contrato', 'periodo_inicio', 'periodo_fin', 'neto_a_pagar')
    list_filter = ('contrato',)

class EvidenciaEsperadaInline(admin.TabularInline):
    model = EvidenciaEsperada
    extra = 1

@admin.register(Obligacion)
class ObligacionAdmin(admin.ModelAdmin):
    list_display = ('numeral', 'contrato', 'descripcion')
    list_filter = ('contrato',)
    ordering = ('contrato', 'numeral')
    inlines = [EvidenciaEsperadaInline]

@admin.register(EvidenciaEsperada)
class EvidenciaEsperadaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'obligacion')
    list_filter = ('obligacion__contrato', 'obligacion__numeral')
    search_fields = ('nombre',)

class EjecucionObligacionInline(admin.StackedInline):
    model = EjecucionObligacion
    extra = 1

@admin.register(InformeMensual)
class InformeMensualAdmin(admin.ModelAdmin):
    list_display = ('mes_reporte', 'contrato', 'fecha_presentacion')
    inlines = [EjecucionObligacionInline]

class EvidenciaObligacionInline(admin.TabularInline):
    model = EvidenciaObligacion
    extra = 1

@admin.register(EjecucionObligacion)
class EjecucionObligacionAdmin(admin.ModelAdmin):
    list_display = ('obligacion', 'informe')
    inlines = [EvidenciaObligacionInline]

@admin.register(EvidenciaObligacion)
class EvidenciaObligacionAdmin(admin.ModelAdmin):
    list_display = ('nombre_archivo', 'ejecucion')

@admin.register(Desplazamiento)
class DesplazamientoAdmin(admin.ModelAdmin):
    list_display = ('numero_orden_viaje', 'lugar', 'fecha_inicial', 'fecha_final')
