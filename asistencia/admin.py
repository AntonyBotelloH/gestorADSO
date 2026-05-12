from django.contrib import admin
from .models import SesionClase, RegistroAsistencia

@admin.register(SesionClase)
class SesionClaseAdmin(admin.ModelAdmin):
    # Columnas que verás en la tabla principal
    list_display = ('fecha', 'ficha', 'tema_tratado', 'cerrada')
    # Filtros laterales
    list_filter = ('fecha', 'ficha', 'cerrada')
    # Barra de búsqueda
    search_fields = ('tema_tratado', 'ficha__codigo_ficha')
    # Navegación por fechas en la parte superior
    date_hierarchy = 'fecha'
    actions = ['marcar_sesion_cerrada', 'desmarcar_sesion_cerrada']

    def marcar_sesion_cerrada(self, request, queryset):
        updated = queryset.update(cerrada=True)
        self.message_user(request, f"Se actualizaron {updated} sesión(es): cerrada marcada.")
    marcar_sesion_cerrada.short_description = "Marcar sesión como cerrada para las selecciones"

    def desmarcar_sesion_cerrada(self, request, queryset):
        updated = queryset.update(cerrada=False)
        self.message_user(request, f"Se actualizaron {updated} sesión(es): cerrada desmarcada.")
    desmarcar_sesion_cerrada.short_description = "Desmarcar sesión cerrada para las selecciones"

@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('aprendiz', 'sesion', 'estado')
    list_filter = ('estado', 'sesion__fecha', 'sesion__ficha')
    # Permite buscar por el nombre o apellido del aprendiz
    search_fields = ('aprendiz__first_name', 'aprendiz__last_name')