from django import forms
from .models import Pendiente
from usuarios.models import Ficha

class PendienteForm(forms.ModelForm):
    
    # Hacemos que la ficha no sea obligatoria en el formulario
    ficha_vinculada = forms.ModelChoiceField(
        queryset=Ficha.objects.filter(is_active=True), 
        required=False,
        label="Vincular a Ficha",
        empty_label="General (Sin Ficha)", # Esto mostrará la opción para no seleccionar ninguna
        widget=forms.Select(attrs={
            'class': 'form-select border-secondary-subtle bg-body text-body shadow-none'
        })
    )

    class Meta:
        model = Pendiente
        # OJO: No incluimos 'instructor' porque se asignará automáticamente desde la vista
        fields = ['descripcion', 'categoria', 'prioridad', 'fecha_limite', 'ficha_vinculada']
        
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control border-secondary-subtle bg-body text-body shadow-none', 
                'placeholder': 'Ej. Calificar evidencias...'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select border-secondary-subtle bg-body text-body shadow-none'
            }),
            'prioridad': forms.Select(attrs={
                'class': 'form-select border-secondary-subtle bg-body text-body shadow-none'
            }),
            'fecha_limite': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control border-secondary-subtle bg-body text-body shadow-none'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Opcional: Si quieres ordenar las fichas por programa o código
        self.fields['ficha_vinculada'].queryset = Ficha.objects.filter(is_active=True).order_by('programa')
