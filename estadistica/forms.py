from django import forms
from .models import InformeMensual, LiquidacionMensual, Contrato, Obligacion

class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = ['numero_contrato', 'objeto_contractual', 'valor_total', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

class ObligacionForm(forms.ModelForm):
    class Meta:
        model = Obligacion
        fields = ['contrato', 'numeral', 'descripcion']

class InformeMensualForm(forms.ModelForm):
    class Meta:
        model = InformeMensual
        # Campos que el usuario llenará al subir un nuevo informe
        fields = ['contrato', 'mes_reporte', 'numero_planilla_pila', 'archivo_informe']

class LiquidacionMensualForm(forms.ModelForm):
    class Meta:
        model = LiquidacionMensual
        fields = '__all__'
        widgets = {
            'periodo_inicio': forms.DateInput(attrs={'type': 'date'}),
            'periodo_fin': forms.DateInput(attrs={'type': 'date'}),
        }