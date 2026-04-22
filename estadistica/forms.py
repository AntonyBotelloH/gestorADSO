from django import forms
from .models import InformeMensual, LiquidacionMensual

class InformeMensualForm(forms.ModelForm):
    class Meta:
        model = InformeMensual
        # Campos que el usuario llenará al subir un nuevo informe
        fields = ['contrato', 'mes_reporte', 'numero_planilla_pila', 'archivo_informe']

class LiquidacionMensualForm(forms.ModelForm):
    class Meta:
        model = LiquidacionMensual
        fields = '__all__'