from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from .models import Contrato, LiquidacionMensual, InformeMensual, Obligacion
from .forms import InformeMensualForm, LiquidacionMensualForm, ContratoForm, ObligacionForm

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

# --- VISTAS PARA CONTRATOS ---
def contrato_list(request):
    contratos = Contrato.objects.all().order_by('-fecha_inicio')
    return render(request, 'estadistica/contrato_list.html', {'contratos': contratos})

def contrato_create(request):
    if request.method == 'POST':
        form = ContratoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contrato_list')
    else:
        form = ContratoForm()
    return render(request, 'estadistica/formulario_base.html', {'form': form, 'titulo': 'Registrar Contrato'})

def contrato_update(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)
    if request.method == 'POST':
        form = ContratoForm(request.POST, instance=contrato)
        if form.is_valid():
            form.save()
            return redirect('contrato_list')
    else:
        form = ContratoForm(instance=contrato)
    return render(request, 'estadistica/formulario_base.html', {'form': form, 'titulo': 'Editar Contrato'})

def contrato_delete(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)
    if request.method == 'POST':
        contrato.delete()
        return redirect('contrato_list')
    return render(request, 'estadistica/confirmar_eliminar.html', {'objeto': contrato, 'tipo': 'Contrato', 'url_cancelar': 'contrato_list'})

# --- VISTAS PARA OBLIGACIONES ---
def obligacion_list(request):
    obligaciones = Obligacion.objects.all().order_by('contrato', 'numeral')
    return render(request, 'estadistica/obligacion_list.html', {'obligaciones': obligaciones})

def obligacion_create(request):
    if request.method == 'POST':
        form = ObligacionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('obligacion_list')
    else:
        form = ObligacionForm()
    return render(request, 'estadistica/formulario_base.html', {'form': form, 'titulo': 'Registrar Obligación'})

def obligacion_update(request, pk):
    obligacion = get_object_or_404(Obligacion, pk=pk)
    if request.method == 'POST':
        form = ObligacionForm(request.POST, instance=obligacion)
        if form.is_valid():
            form.save()
            return redirect('obligacion_list')
    else:
        form = ObligacionForm(instance=obligacion)
    return render(request, 'estadistica/formulario_base.html', {'form': form, 'titulo': 'Editar Obligación'})

def obligacion_delete(request, pk):
    obligacion = get_object_or_404(Obligacion, pk=pk)
    if request.method == 'POST':
        obligacion.delete()
        return redirect('obligacion_list')
    return render(request, 'estadistica/confirmar_eliminar.html', {'objeto': obligacion, 'tipo': 'Obligación', 'url_cancelar': 'obligacion_list'})


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
            return redirect('informe_list')
    else:
        form = InformeMensualForm()
        
    return render(request, 'estadistica/formulario_base.html', {'form': form, 'titulo': 'Subir Informe Mensual'})


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
            return redirect('liquidacion_list')
    else:
        form = LiquidacionMensualForm()
        
    return render(request, 'estadistica/formulario_base.html', {'form': form, 'titulo': 'Registrar Liquidación'})