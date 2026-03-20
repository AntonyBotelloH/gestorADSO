from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.forms import DateInput
from django.db import models
from .models import Ficha, Usuario, GrupoProyecto, UsuarioAuditoria

@admin.register(Usuario)
class UsuarioCustomAdmin(UserAdmin):
    # Columnas que verás en la tabla principal del panel
    list_display = ('username', 'documento', 'first_name', 'last_name', 'rol', 'ficha', 'edad', 'is_active')
    
    # El filtro lateral que causaba el error (ahora usa 'rol')
    list_filter = ('rol', 'is_staff', 'is_active', 'ficha')
    
    # Barra de búsqueda
    search_fields = ('username', 'first_name', 'last_name', 'documento')
    
    # Agrupación de campos al ver o editar un usuario
    fieldsets = UserAdmin.fieldsets + (
        ('Información SENA', {'fields': ('tipo_documento', 'documento', 'rol', 'ficha', 'fecha_nacimiento')}),
    )
    
    # Campos que aparecen al crear un usuario nuevo desde cero
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información SENA', {'fields': ('tipo_documento', 'documento', 'rol', 'ficha', 'fecha_nacimiento')}),
    )
    
    # Para que los campos DateField usen input type="date"
    formfield_overrides = {
        models.DateField: {'widget': DateInput(attrs={'type': 'date'})},
    }
    
    def save_model(self, request, obj, form, change):
        # Si es una edición (no creación), registrar en auditoría
        if change:
            UsuarioAuditoria.objects.create(
                usuario_editado=obj,
                editor=request.user,
                ip_editor=self.get_client_ip(request),
                cambios="Edición desde admin"  # Puedes personalizar esto
            )
        super().save_model(request, obj, form, change)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.fecha_nacimiento:
            form.base_fields['fecha_nacimiento'].initial = obj.fecha_nacimiento.strftime('%Y-%m-%d')
        return form

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

@admin.register(UsuarioAuditoria)
class UsuarioAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('usuario_editado', 'editor', 'ip_editor', 'fecha_edicion')
    list_filter = ('fecha_edicion', 'editor')
    search_fields = ('usuario_editado__username', 'editor__username', 'ip_editor')
    readonly_fields = ('usuario_editado', 'editor', 'ip_editor', 'fecha_edicion', 'cambios')