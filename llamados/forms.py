from django import forms
from .models import LlamadoAtencion, EstrategiaPedagogica, PlanMejoramiento
from usuarios.models import Usuario

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
            }),
            'fecha_fin': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control border-secondary-subtle bg-body-tertiary text-body shadow-none'
            }),
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
        # Agregamos los nuevos campos a la lista
        fields = ['aprendiz', 'tipo_falta', 'gravedad', 'instancia', 'motivo_principal', 'descripcion']
        
        widgets = {
            'aprendiz': forms.Select(attrs={'class': 'form-select border-secondary-subtle bg-body-tertiary text-body shadow-none'}),
            # Widgets para los nuevos campos
            'tipo_falta': forms.Select(attrs={'class': 'form-select border-secondary-subtle bg-body-tertiary text-body shadow-none'}),
            'gravedad': forms.Select(attrs={'class': 'form-select border-secondary-subtle bg-body-tertiary text-body shadow-none'}),
            
            'instancia': forms.Select(attrs={'class': 'form-select border-secondary-subtle bg-body-tertiary text-body shadow-none'}),
            'motivo_principal': forms.TextInput(attrs={'class': 'form-control border-secondary-subtle bg-body-tertiary text-body shadow-none', 'placeholder': 'Ej. Plagio, Inasistencia, Agresión...'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control border-secondary-subtle bg-body-tertiary text-body shadow-none', 'rows': 4, 'placeholder': 'Detalle objetivamente la situación ocurrida...'}),
        }

    def __init__(self, ficha_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtramos dinámicamente los aprendices
        if ficha_id:
            # Nota: Asegúrate de que esta consulta coincida con cómo relacionaste Usuario y Ficha en tu proyecto.
            # Si un aprendiz pertenece a una ficha mediante un campo ForeignKey llamado 'ficha':
            self.fields['aprendiz'].queryset = Usuario.objects.filter(rol='APRENDIZ', ficha__codigo_ficha=ficha_id)
            self.fields['aprendiz'].empty_label = "-- Seleccione el aprendiz implicado --"
        else:
            # Si por alguna razón no hay ficha, vaciamos la lista por seguridad
            self.fields['aprendiz'].queryset = Usuario.objects.none()
            

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