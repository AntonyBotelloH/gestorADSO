from django import forms
from .models import LlamadoAtencion, EstrategiaPedagogica, PlanMejoramiento, FaltaReglamento
from usuarios.models import Usuario

class PlanMejoramientoCrearForm(forms.ModelForm):
    class Meta:
        model = PlanMejoramiento
        fields = ['estrategias', 'fecha_inicio', 'fecha_fin', 'observaciones']
        
        widgets = {
            'estrategias': forms.SelectMultiple(attrs={
                'class': 'form-select border-secondary-subtle bg-body-tertiary text-body shadow-none', 
                'style': 'height: 120px;',
                'help_text': 'Mantén presionado Ctrl (Windows) o Cmd (Mac) para seleccionar varias.'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control border-secondary-subtle bg-body-tertiary text-body shadow-none'
            }, format='%Y-%m-%d'),
            'fecha_fin': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control border-secondary-subtle bg-body-tertiary text-body shadow-none'
            }, format='%Y-%m-%d'),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control border-secondary-subtle bg-body-tertiary text-body shadow-none', 
                'rows': 3, 
                'placeholder': 'Instrucciones o notas adicionales para el aprendiz...'
            }),
        }

class PlanMejoramientoForm(forms.ModelForm):
    class Meta:
        model = PlanMejoramiento
        fields = ['estrategias', 'fecha_inicio', 'fecha_fin', 'estado', 'observaciones']
        
        widgets = {
            'estrategias': forms.SelectMultiple(attrs={
                'class': 'form-select border-secondary-subtle bg-body-tertiary text-body shadow-none', 
                'style': 'height: 120px;',
                'help_text': 'Mantén presionado Ctrl (Windows) o Cmd (Mac) para seleccionar varias.'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control border-secondary-subtle bg-body-tertiary text-body shadow-none'
            }, format='%Y-%m-%d'),
            'fecha_fin': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control border-secondary-subtle bg-body-tertiary text-body shadow-none'
            }, format='%Y-%m-%d'),
            'estado': forms.Select(attrs={
                'class': 'form-select border-secondary-subtle bg-body-tertiary text-body shadow-none'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control border-secondary-subtle bg-body-tertiary text-body shadow-none', 
                'rows': 3, 
                'placeholder': 'Instrucciones o notas adicionales para el aprendiz...'
            }),
        }

class LlamadoAtencionForm(forms.ModelForm):
    class Meta:
        model = LlamadoAtencion
        # OJO: Cambiamos motivo_principal por falta_cometida
        fields = ['aprendiz', 'falta_cometida', 'tipo_falta', 'gravedad', 'instancia', 'descripcion']
        
        widgets = {
            'aprendiz': forms.Select(attrs={
                'class': 'form-select select2-busqueda border-secondary-subtle bg-body-tertiary text-body shadow-none'
            }),
            # El nuevo catálogo del Acuerdo 009
            'falta_cometida': forms.Select(attrs={
                'class': 'form-select select2-busqueda border-secondary-subtle bg-body-tertiary text-body shadow-none'
            }),
            # Estos dos se llenarán solos con JavaScript, les ponemos una clase visual para diferenciarlos
            'tipo_falta': forms.Select(attrs={
                'class': 'form-select border-secondary-subtle bg-secondary text-white shadow-none bg-opacity-25'
            }),
            'gravedad': forms.Select(attrs={
                'class': 'form-select border-secondary-subtle bg-secondary text-white shadow-none bg-opacity-25'
            }),
            'instancia': forms.Select(attrs={
                'class': 'form-select border-secondary-subtle bg-body-tertiary text-body shadow-none'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control border-secondary-subtle bg-body-tertiary text-body shadow-none', 
                'rows': 4, 
                'placeholder': 'Detalle objetivamente la situación ocurrida...'
            }),
        }

    def __init__(self, ficha_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtramos dinámicamente los aprendices y voceros de la ficha
        if ficha_id:
            self.fields['aprendiz'].queryset = Usuario.objects.filter(
                rol__in=['APRENDIZ', 'VOCERO'], 
                ficha__codigo_ficha=ficha_id
            ).order_by('first_name')
            self.fields['aprendiz'].empty_label = "-- Seleccione el aprendiz implicado --"
        else:
            self.fields['aprendiz'].queryset = Usuario.objects.none()
            
        # Filtro estético para el catálogo normativo
        self.fields['falta_cometida'].empty_label = "-- Busque y seleccione la tipificación de la falta --"


class EstrategiaPedagogicaForm(forms.ModelForm):
    class Meta:
        model = EstrategiaPedagogica
        fields = ['nombre', 'descripcion', 'plazo_dias']
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control border-secondary-subtle bg-body text-body shadow-none', 
                'placeholder': 'Ej. Taller de nivelación'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control border-secondary-subtle bg-body text-body shadow-none', 
                'placeholder': 'Detalle la actividad...'
            }),
            'plazo_dias': forms.NumberInput(attrs={
                'class': 'form-control border-secondary-subtle bg-body text-body shadow-none',
                'placeholder': 'Ej. 5',
                'min': '1'
            }),
        }

class DescargoForm(forms.ModelForm):
    """Formulario para que el instructor registre el descargo del aprendiz."""
    class Meta:
        model = LlamadoAtencion
        fields = ['descargo_aprendiz']
        widgets = {
            'descargo_aprendiz': forms.Textarea(
                attrs={
                    'rows': 6, 
                    'class': 'form-control',
                    'placeholder': 'Escribe aquí la versión de los hechos presentada por el aprendiz...'
                }
            ),
        }
        labels = {
            'descargo_aprendiz': 'Versión de los hechos presentada por el aprendiz:'
        }