
from django import forms

from planeacion.models import ActividadPlaneacion, Competencia, ResultadoAprendizaje

class ActividadPlaneacionForm(forms.ModelForm):
    class Meta:
        model = ActividadPlaneacion
        # Excluimos 'ficha' porque se la asignaremos automáticamente en el views.py
        fields = ['fase', 'raps', 'instructor', 'actividad_proyecto', 'fecha_inicio', 'fecha_fin', 'estado']
        
        widgets = {
            'fecha_inicio': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'fecha_fin': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'actividad_proyecto': forms.Textarea(
                attrs={'rows': 3, 'placeholder': 'Describe la actividad de proyecto...'}
            ),
        }


class CompetenciaForm(forms.ModelForm):
    class Meta:
        model = Competencia
        fields = ['codigo', 'nombre', 'duracion_horas']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '220501096'}),
            'nombre': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Nombre de la competencia'}),
            'duracion_horas': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class ResultadoAprendizajeForm(forms.ModelForm):
    class Meta:
        model = ResultadoAprendizaje
        fields = ['competencia', 'descripcion']
        widgets = {
            'competencia': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del RAP'}),
        }