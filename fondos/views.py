from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from usuarios.decorators import rol_requerido
from .models import Concepto, Movimiento, MetaFinanciera
from usuarios.models import Ficha, Usuario

@login_required
def dashboard_fondos(request):
    """Vista principal: Dashboard financiero y registro de movimientos (lectura para todos, escritura solo Instructor/Admin)."""
    ficha_id = request.session.get('ficha_activa_id')
    
    if not ficha_id:
        messages.warning(request, "Por favor, selecciona una ficha primero.")
        return redirect('inicio')

    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)

    # --- LÓGICA DE GUARDADO (POST) - SOLO VOCERO/ADMIN ---
    if request.method == 'POST':
        # Verificar que el usuario sea Vocero o Admin para registrar movimientos
        if request.user.rol not in ['VOCERO', 'Admin']:
            messages.error(request, "No tienes permiso para registrar movimientos.")
            return redirect('inicio_fondos')
        
        concepto_id = request.POST.get('concepto')
        responsable_id = request.POST.get('responsable')
        valor = request.POST.get('valor')
        
        concepto_obj = get_object_or_404(Concepto, id=concepto_id)
        # Los ingresos por defecto quedan como 'Pendiente' (por cobrar)
        # Los egresos se marcan como 'Ejecutado' de inmediato.
        estado_inicial = 'Pendiente' if concepto_obj.tipo_operacion == 'Ingreso' else 'Ejecutado'
        responsable_obj = Usuario.objects.filter(id=responsable_id).first() if responsable_id else None

        Movimiento.objects.create(
            ficha=ficha,
            responsable=responsable_obj,
            concepto=concepto_obj,
            valor=valor,
            estado=estado_inicial,
            # Si se cobra/paga de una vez, la fecha de pago es HOY. Si queda pendiente, es None.
            fecha_pago=timezone.now() if estado_inicial == 'Ejecutado' else None
        )
        messages.success(request, "Movimiento registrado exitosamente.")
        return redirect('inicio_fondos')

    # --- LÓGICA DE LECTURA (GET) ---
    
    # 1. Cálculos de Caja Real (Solo lo que ya se pagó/ejecutó)
    ingresos_ejecutados = Movimiento.objects.filter(
        ficha=ficha, 
        concepto__tipo_operacion='Ingreso', 
        estado='Ejecutado'
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    
    egresos_ejecutados = Movimiento.objects.filter(
        ficha=ficha, 
        concepto__tipo_operacion='Egreso', 
        estado='Ejecutado'
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    
    caja_real = ingresos_ejecutados - egresos_ejecutados

    # 2. Cartera (Dinero pendiente de cobro)
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
        # El progreso se basa en lo recaudado (ingresos ejecutados)
        progreso = min((ingresos_ejecutados / meta.valor_objetivo) * 100, 100)
        faltante = max(meta.valor_objetivo - ingresos_ejecutados, 0)

    contexto = {
        'caja_real': caja_real,
        'cartera': cartera,
        'meta': meta,
        'progreso_meta': round(progreso, 1),
        'faltante_meta': faltante,
        'movimientos': Movimiento.objects.filter(ficha=ficha).select_related('concepto', 'responsable').order_by('-fecha')[:10],
        'conceptos_activos': Concepto.objects.filter(activo=True),
        'aprendices': Usuario.objects.filter(rol='APRENDIZ'), 
        # Variable para tu partial de breadcrumbs
        'breadcrumbs': [
            {'nombre': 'Fondos', 'url': '/fondos/'}
        ]
    }

    return render(request, 'fondos/fondos.html', contexto)


@login_required
def listar_conceptos(request):
    """Vista para configurar las tarifas y multas (lectura para todos, escritura solo Instructor/Admin)."""
    if request.method == 'POST':
        # Verificar que sea Vocero o Admin para crear conceptos
        if request.user.rol not in ['VOCERO', 'Admin']:
            messages.error(request, "No tienes permiso para crear conceptos.")
            return redirect('conceptos')
        
        categoria = request.POST.get('categoria')
        Concepto.objects.create(
            nombre=request.POST.get('nombre'),
            categoria=categoria,
            tipo_operacion='Egreso' if categoria == 'Gasto' else 'Ingreso',
            valor_sugerido=request.POST.get('valor_sugerido'),
            vigente_desde=request.POST.get('vigente_desde'),
            activo=request.POST.get('estado') == 'Activo'
        )
        messages.success(request, "Concepto guardado en el catálogo.")
        return redirect('conceptos')

    conceptos = Concepto.objects.all().order_by('categoria', 'nombre')
    contexto = {
        'conceptos': conceptos,
        'breadcrumbs': [
            {'nombre': 'Fondos', 'url': '/fondos/'},
            {'nombre': 'Catálogo de Conceptos', 'url': ''}
        ]
    }
    return render(request, 'fondos/conceptos.html', contexto)


@login_required
def ver_recibo(request, movimiento_id):
    """Genera la vista de detalle de un comprobante específico (lectura)."""
    movimiento = get_object_or_404(Movimiento, id=movimiento_id)
    contexto = {
        'movimiento': movimiento,
        'breadcrumbs': [
            {'nombre': 'Fondos', 'url': '/fondos/'},
            {'nombre': f'Comprobante #{movimiento.id:04d}', 'url': ''}
        ]
    }
    return render(request, 'fondos/recibo.html', contexto)

@login_required
@rol_requerido('INSTRUCTOR', 'Admin')
def pagar_movimiento(request, movimiento_id):
    """Cambia el estado de un movimiento de Pendiente a Ejecutado y registra la fecha."""
    if request.method == 'POST':
        movimiento = get_object_or_404(Movimiento, id=movimiento_id)
        
        if movimiento.estado == 'Pendiente':
            movimiento.estado = 'Ejecutado'
            # Registramos el momento exacto en el que el instructor le dio clic al botón
            movimiento.fecha_pago = timezone.now() 
            movimiento.save()
            
            messages.success(request, f"¡El pago de $ {movimiento.valor:,.0f} fue registrado exitosamente!")
            
    return redirect('inicio_fondos')
@login_required
def configurar_metas(request):
    """Vista para establecer el objetivo financiero (lectura para todos, escritura solo Instructor/Admin)."""
    ficha_id = request.session.get('ficha_activa_id')
    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id) if ficha_id else None

    # Si entra un formulario por POST - SOLO INSTRUCTOR/ADMIN
    if request.method == 'POST' and ficha:
        # Verificar que sea Admin
        if request.user.rol != 'Admin':
            messages.error(request, "No tienes permiso para crear o modificar metas.")
            return redirect('metas')
        
        # Desactivar otras metas para que solo haya una principal activa
        MetaFinanciera.objects.filter(ficha=ficha).update(activa=False)
        
        MetaFinanciera.objects.create(
            ficha=ficha,
            nombre=request.POST.get('nombre'),
            descripcion=request.POST.get('descripcion'),
            valor_objetivo=request.POST.get('valor_objetivo'),
            fecha_limite=request.POST.get('fecha_limite'),
            activa=True
        )
        messages.success(request, "Nueva meta establecida para la ficha.")
        return redirect('metas')

    # Lógica de Lectura para mostrar la tarjeta de la derecha
    meta_activa = MetaFinanciera.objects.filter(ficha=ficha, activa=True).first() if ficha else None
    
    recaudado = 0
    progreso = 0
    faltante = 0

    if meta_activa:
        # Solo contamos ingresos que YA fueron pagados (Ejecutados)
        recaudado = Movimiento.objects.filter(
            ficha=ficha, 
            concepto__tipo_operacion='Ingreso', 
            estado='Ejecutado'
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        
        if meta_activa.valor_objetivo > 0:
            progreso = min((recaudado / meta_activa.valor_objetivo) * 100, 100)
            
        # Calculamos el faltante restando lo recaudado del objetivo
        faltante = max(meta_activa.valor_objetivo - recaudado, 0)

    # Obtener todas las metas de la ficha para el histórico
    todas_metas = MetaFinanciera.objects.filter(ficha=ficha).order_by('-activa', '-fecha_limite') if ficha else []

    contexto = {
        'titulo': 'Metas de Fondo',
        'meta_activa': meta_activa,
        'recaudado': recaudado,
        'progreso': round(progreso, 1),
        'faltante': faltante, # <--- Enviamos el faltante ya calculado al HTML
        'todas_metas': todas_metas,
        'breadcrumbs': [
            {'nombre': 'Fondos', 'url': '/fondos/'},
            {'nombre': 'Metas Financieras', 'url': ''}
        ]
    }
    return render(request, 'fondos/metas.html', contexto)

@login_required
@rol_requerido('Admin')
def editar_meta(request, meta_id):
    """Vista para editar una meta financiera (solo Admin)."""
    meta = get_object_or_404(MetaFinanciera, id=meta_id)
    
    if request.method == 'POST':
        meta.nombre = request.POST.get('nombre', meta.nombre)
        meta.descripcion = request.POST.get('descripcion', meta.descripcion)
        meta.valor_objetivo = request.POST.get('valor_objetivo', meta.valor_objetivo)
        meta.fecha_limite = request.POST.get('fecha_limite', meta.fecha_limite)
        meta.save()
        
        messages.success(request, "Meta actualizada correctamente.")
        return redirect('metas')
    
    contexto = {
        'meta': meta,
        'titulo': f'Editar Meta: {meta.nombre}',
        'breadcrumbs': [
            {'nombre': 'Fondos', 'url': '/fondos/'},
            {'nombre': 'Metas Financieras', 'url': '/fondos/metas/'},
            {'nombre': 'Editar Meta', 'url': ''}
        ]
    }
    return render(request, 'fondos/editar_meta.html', contexto)

@login_required
@rol_requerido('INSTRUCTOR', 'Admin')
def activar_meta(request, meta_id):
    """Vista para activar una meta (desactiva las demás de la misma ficha)."""
    meta = get_object_or_404(MetaFinanciera, id=meta_id)
    ficha = meta.ficha
    
    # Desactivar todas las metas de la ficha
    MetaFinanciera.objects.filter(ficha=ficha).update(activa=False)
    
    # Activar la meta seleccionada
    meta.activa = True
    meta.save()
    
    messages.success(request, f"Meta '{meta.nombre}' establecida como activa.")
    return redirect('metas')

@login_required
@rol_requerido('INSTRUCTOR', 'Admin')
def finalizar_meta(request, meta_id):
    """Vista para finalizar/cerrar una meta."""
    meta = get_object_or_404(MetaFinanciera, id=meta_id)
    
    # Desactivar la meta
    meta.activa = False
    meta.save()
    
    messages.success(request, f"Meta '{meta.nombre}' finalizada.")
    return redirect('metas')