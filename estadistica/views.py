from urllib import request

from django.shortcuts import render, redirect
from django.db.models import Sum
from .models import Contrato, LiquidacionMensual, InformeMensual
from .forms import InformeMensualForm, LiquidacionMensualForm

def dashboard_sena(request):
    """Vista principal con el resumen estadístico de los contratos."""
    contratos = Contrato.objects.all()
    
    # Cálculos estadísticos globales
    total_facturado = LiquidacionMensual.objects.aggregate(total=Sum('valor_bruto'))['total'] or 0
    total_neto_recibido = LiquidacionMensual.objects.aggregate(total=Sum('neto_a_pagar'))['total'] or 0
    
    gasto_total_pila = LiquidacionMensual.objects.aggregate(
        total=Sum('aporte_salud') + Sum('aporte_pension') + Sum('aporte_arl')
    )['total'] or 0

    context = {
        'contratos': contratos,
        'total_facturado': total_facturado,
        'total_neto_recibido': total_neto_recibido,
        'gasto_total_pila': gasto_total_pila,
    }
    return render(request, 'dashboard.html', context)


# --- VISTAS PARA INFORMES MENSUALES ---

def informe_list(request):
    """Lista todos los informes ordenados por el más reciente."""
    informes = InformeMensual.objects.all().order_by('-fecha_presentacion')
    return render(request, 'estadistica/informe_list.html', {'informes': informes})

def informe_create(request):
    """Maneja el formulario para crear un nuevo informe y subir el PDF."""
    if request.method == 'POST':
        # request.FILES es indispensable para poder guardar el PDF
        form = InformeMensualForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('sena:informe_list')
    else:
        form = InformeMensualForm()
        
    return render(request, 'estadistica/formulario_base.html', {'form': form})


# --- VISTAS PARA LIQUIDACIONES (PAGOS) ---

def liquidacion_list(request):
    """Lista los pagos ordenados por el número de pago."""
    liquidaciones = LiquidacionMensual.objects.all().order_by('-numero_pago')
    return render(request, 'estadistica/liquidacion_list.html', {'liquidaciones': liquidaciones})

def liquidacion_create(request):
    """Maneja el formulario para registrar una nueva liquidación."""
    if request.method == 'POST':
        form = LiquidacionMensualForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('sena:liquidacion_list')
    else:
        form = LiquidacionMensualForm()
        
    return render(request, 'estadistica/formulario_base.html', {'form': form})