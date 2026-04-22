from django import forms
from django.forms import ModelForm, DateInput
from django.contrib.admin.widgets import FilteredSelectMultiple
from .models import Usuario, Ficha, GrupoProyecto

# ==========================================
# FORMULARIOS DE USUARIO
# ==========================================

class UsuarioForm(ModelForm):

    class Meta:
        model = Usuario
        # Al heredar de AbstractUser, es peligroso usar "__all__". 
        # Es mejor definir exactamente qué campos puede llenar el administrador.
        fields = [
            'first_name', 'last_name', 'email', 
            'tipo_documento', 'documento', 'rol', 'ficha','foto', 'fecha_nacimiento'
        ]
        
        widgets = {
            'fecha_nacimiento': DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    
class UsuarioEditarForm(ModelForm):
    class Meta:
        model = Usuario
        # En la edición, excluimos el documento y la contraseña por seguridad.
        # Agregamos 'is_active' por si necesitas desactivar a un aprendiz que se retiró.
        fields = [
            'first_name', 'last_name', 'email', 
            'tipo_documento', 'rol', 'ficha', 'is_active','foto', 'fecha_nacimiento'
        ]
        
        widgets = {
            'fecha_nacimiento': DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }


# ==========================================
# FORMULARIOS DE FICHA
# ==========================================

class FichaForm(ModelForm):
    class Meta:
        model = Ficha
        # Es mejor listar los campos para controlar el orden en el HTML
        fields = [
            'codigo_ficha', 
            'programa', 
            'jornada', 
            'fecha_inicio', 
            'fecha_fin_lectiva', 
            'etapa', 
        ]
        
        # Le decimos a Django que los campos de fecha usen el input type="date" de HTML5
        widgets = {
            'fecha_inicio': DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'fecha_fin_lectiva': DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
        }


class FichaEditarForm(ModelForm):
    class Meta:
        model = Ficha
        # En la edición excluimos 'codigo_ficha' por seguridad e incluimos 'is_active'
        fields = [
            'programa', 
            'jornada', 
            'fecha_inicio', 
            'fecha_fin_lectiva', 
            'etapa',
            'is_active',
        ]
        
        widgets = {
            'fecha_inicio': DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'fecha_fin_lectiva': DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
        }

# ==========================================
# FORMULARIOS DE GRUPO DE PROYECTO (SCRUM)
# ==========================================

class GrupoProyectoForm(ModelForm):
    # Adaptación de tu ejemplo con FilteredSelectMultiple para el ManyToMany
    integrantes = forms.ModelMultipleChoiceField(
        # Filtro inteligente: Solo permite agregar a los que tienen rol de APRENDIZ
        queryset=Usuario.objects.filter(rol='APRENDIZ', is_active=True),
        widget=FilteredSelectMultiple('Integrantes', is_stacked=False),
        required=False,
    )

    class Meta:
        model = GrupoProyecto
        fields = ['nombre', 'integrantes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        # Nota: El widget FilteredSelectMultiple tiene sus propios estilos del admin de Django.