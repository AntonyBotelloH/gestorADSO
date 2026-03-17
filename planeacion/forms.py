
from django import forms

from planeacion.models import ActividadPlaneacion

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