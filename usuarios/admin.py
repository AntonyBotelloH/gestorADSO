from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Ficha, Usuario, GrupoProyecto

@admin.register(Usuario)
class UsuarioCustomAdmin(UserAdmin):
    # Columnas que verás en la tabla principal del panel
    list_display = ('username', 'documento', 'first_name', 'last_name', 'rol', 'ficha', 'is_active')
    
    # El filtro lateral que causaba el error (ahora usa 'rol')
    list_filter = ('rol', 'is_staff', 'is_active', 'ficha')
    
    # Barra de búsqueda
    search_fields = ('username', 'first_name', 'last_name', 'documento')
    
    # Agrupación de campos al ver o editar un usuario
    fieldsets = UserAdmin.fieldsets + (
        ('Información SENA', {'fields': ('tipo_documento', 'documento', 'rol', 'ficha')}),
    )
    
    # Campos que aparecen al crear un usuario nuevo desde cero
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información SENA', {'fields': ('tipo_documento', 'documento', 'rol', 'ficha')}),
    )

@admin.register(Ficha)
class FichaAdmin(admin.ModelAdmin):
    list_display = ('codigo_ficha', 'programa', 'jornada')
    search_fields = ('codigo_ficha', 'programa')
    list_filter = ('jornada',)

@admin.register(GrupoProyecto)
class GrupoProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)
    # Crea una interfaz amigable de dos columnas para seleccionar los integrantes
    filter_horizontal = ('integrantes',)