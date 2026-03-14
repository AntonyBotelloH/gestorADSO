from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from .models import Concepto, Movimiento, MetaFinanciera
from usuarios.models import Ficha, Usuario

def dashboard_fondos(request):
    """Vista principal: Dashboard financiero y registro de movimientos."""
    ficha_id = request.session.get('ficha_activa_id')
    
    if not ficha_id:
        messages.warning(request, "Por favor, selecciona una ficha primero.")
        return redirect('inicio') # O donde tengas tu selector principal

    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)

    # --- LÓGICA DE GUARDADO (POST) ---
    if request.method == 'POST':
        concepto_id = request.POST.get('concepto')
        responsable_id = request.POST.get('responsable')
        valor = request.POST.get('valor')
        
        # Como es el dashboard, asumimos que si es un ingreso (como una multa), puede quedar pendiente.
        # Si es un egreso (gasto), normalmente se ejecuta de inmediato.
        concepto_obj = get_object_or_404(Concepto, id=concepto_id)
        estado_inicial = 'Pendiente' if concepto_obj.tipo_operacion == 'Ingreso' else 'Ejecutado'

        responsable_obj = Usuario.objects.filter(id=responsable_id).first() if responsable_id else None

        Movimiento.objects.create(
            ficha=ficha,
            responsable=responsable_obj,
            concepto=concepto_obj,
            valor=valor,
            estado=estado_inicial
        )
        messages.success(request, "Movimiento registrado exitosamente.")
        return redirect('fondos')

    # --- LÓGICA DE LECTURA (GET) ---
    
    # 1. Cálculos de Caja Real (Solo ejecutados)
    ingresos = Movimiento.objects.filter(
        ficha=ficha, 
        concepto__tipo_operacion='Ingreso', 
        estado='Ejecutado'
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    
    egresos = Movimiento.objects.filter(
        ficha=ficha, 
        concepto__tipo_operacion='Egreso', 
        estado='Ejecutado'
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    
    caja_real = ingresos - egresos

    # 2. Cartera (Plata que deben los aprendices)
    cartera = Movimiento.objects.filter(
        ficha=ficha, 
        concepto__tipo_operacion='Ingreso', 
        estado='Pendiente'
    ).aggregate(Sum('valor'))['valor__sum'] or 0

    # 3. Meta Activa
    meta = MetaFinanciera.objects.filter(ficha=ficha, activa=True).first()
    progreso = 0
    faltante = 0
    if meta and meta.valor_objetivo > 0:
        progreso = min((ingresos / meta.valor_objetivo) * 100, 100) # Evitar que pase del 100% visualmente
        faltante = max(meta.valor_objetivo - ingresos, 0)

    contexto = {
        'titulo': 'Panel de Control del Tesorero',
        'caja_real': caja_real,
        'cartera': cartera,
        'meta': meta,
        'progreso_meta': round(progreso, 1),
        'faltante_meta': faltante,
        'movimientos': Movimiento.objects.filter(ficha=ficha).select_related('concepto', 'responsable')[:10],
        'conceptos_activos': Concepto.objects.filter(activo=True),
        'aprendices': Usuario.objects.filter(rol='APRENDIZ') # Ajusta esto según cómo relaciones aprendices y fichas
    }

    return render(request, 'fondos/fondos.html', contexto)


def listar_conceptos(request):
    """Vista para configurar las tarifas y multas."""
    if request.method == 'POST':
        Concepto.objects.create(
            nombre=request.POST.get('nombre'),
            categoria=request.POST.get('categoria'),
            tipo_operacion='Egreso' if request.POST.get('categoria') == 'Gasto' else 'Ingreso',
            valor_sugerido=request.POST.get('valor_sugerido'),
            vigente_desde=request.POST.get('vigente_desde'),
            activo=request.POST.get('estado') == 'Activo'
        )
        messages.success(request, "Concepto guardado en el catálogo.")
        return redirect('conceptos')

    conceptos = Concepto.objects.all()
    return render(request, 'fondos/conceptos.html', {'conceptos': conceptos})


def configurar_metas(request):
    """Vista para establecer el objetivo financiero (ej. Salida técnica)."""
    ficha_id = request.session.get('ficha_activa_id')
    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id) if ficha_id else None

    if request.method == 'POST' and ficha:
        # Desactivar metas anteriores de esta ficha
        MetaFinanciera.objects.filter(ficha=ficha).update(activa=False)
        
        # Crear nueva meta
        MetaFinanciera.objects.create(
            
            ficha=ficha,
            nombre=request.POST.get('nombre'),
            descripcion=request.POST.get('descripcion'),
            valor_objetivo=request.POST.get('valor_objetivo'),
            fecha_limite=request.POST.get('fecha_limite'),
            activa=True
        )
        messages.success(request, "Nueva meta establecida.")
        return redirect('metas')

    meta_activa = MetaFinanciera.objects.filter(ficha=ficha, activa=True).first() if ficha else None
    
    # Calcular recaudo para la meta activa
    recaudado = 0
    if meta_activa:
        recaudado = Movimiento.objects.filter(
            ficha=ficha, 
            concepto__tipo_operacion='Ingreso', 
            estado='Ejecutado'
        ).aggregate(Sum('valor'))['valor__sum'] or 0

    contexto = {
        'titulo': 'Configuración de Metas Financieras',
        'meta_activa': meta_activa,
        'recaudado': recaudado,
        'progreso': min((recaudado / meta_activa.valor_objetivo) * 100, 100) if meta_activa and meta_activa.valor_objetivo else 0
    }
    return render(request, 'fondos/metas.html', contexto)


def ver_recibo(request, movimiento_id):
    """Genera la vista de detalle de un comprobante específico."""
    movimiento = get_object_or_404(Movimiento, id=movimiento_id)
    return render(request, 'fondos/recibo.html', {'movimiento': movimiento})