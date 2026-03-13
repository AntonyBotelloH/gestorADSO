from django import forms
from django.forms import ModelForm
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
            'tipo_documento', 'documento', 'rol', 'ficha','foto'
        ]

    
class UsuarioEditarForm(ModelForm):
    class Meta:
        model = Usuario
        # En la edición, excluimos el documento y la contraseña por seguridad.
        # Agregamos 'is_active' por si necesitas desactivar a un aprendiz que se retiró.
        fields = [
            'first_name', 'last_name', 'email', 
            'tipo_documento', 'rol', 'ficha', 'is_active','foto'
        ]

   
# ==========================================
# FORMULARIOS DE FICHA
# ==========================================

class FichaForm(ModelForm):
    class Meta:
        model = Ficha
        fields = "__all__"

   

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