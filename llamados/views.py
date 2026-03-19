from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import LlamadoAtencion, EstrategiaPedagogica, PlanMejoramiento
from .forms import EstrategiaPedagogicaForm, LlamadoAtencionForm, PlanMejoramientoForm
from usuarios.models import Ficha

def listar_llamados(request):
    """Vista principal para registrar y listar los llamados de atención de una ficha."""
    ficha_id = request.session.get('ficha_activa_id')
    llamados = []
    form = None
    
    # Si no hay ficha seleccionada, mostramos la vista vacía con la advertencia
    if not ficha_id:
        messages.warning(request, "Selecciona una ficha para gestionar el control disciplinario.")
        return render(request, 'llamados/llamados.html', {'ficha_activa': None})

    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)
    
    # Procesar el formulario si se envía por POST
    if request.method == 'POST':
        # Pasamos ficha_id y request.FILES por si a futuro decides subir actas en PDF desde aquí
        form = LlamadoAtencionForm(ficha_id, request.POST, request.FILES)
        if form.is_valid():
            llamado = form.save(commit=False)
            llamado.ficha = ficha
            llamado.save()
            messages.success(request, "Novedad disciplinaria registrada con éxito.")
            return redirect('listar_llamados')
        else:
            messages.error(request, "Revisa los errores en el formulario.")
    else:
        # Formulario limpio
        form = LlamadoAtencionForm(ficha_id=ficha_id)

    # Traer el historial de llamados de esta ficha específica (select_related mejora el rendimiento)
    llamados = LlamadoAtencion.objects.filter(ficha=ficha).select_related('aprendiz')

    context = {
        'titulo': 'Control Disciplinario',
        'ficha_activa': ficha,
        'form': form,
        'llamados': llamados,
        'breadcrumbs': [{'nombre': 'Llamados de Atención', 'url': ''}]
    }
    return render(request, 'llamados/llamados.html', context)

def crear_plan(request, llamado_id):
    """Vista para crear un plan de mejoramiento amarrado a un llamado específico"""
    llamado = get_object_or_404(LlamadoAtencion, pk=llamado_id)
    
    # Validamos que no tenga un plan ya creado (relación OneToOne)
    if hasattr(llamado, 'plan_mejoramiento'):
        messages.warning(request, "Este caso ya tiene un plan de mejoramiento asignado.")
        return redirect('detalle_llamado', pk=llamado.id)
        
    if request.method == 'POST':
        form = PlanMejoramientoForm(request.POST)
        if form.is_valid():
            # Guardamos con commit=False para poder asociarle el llamado
            plan = form.save(commit=False)
            plan.llamado = llamado
            plan.save()
            
            # Obligatorio en Django al guardar un ManyToManyField (las estrategias)
            form.save_m2m() 
            
            messages.success(request, f"Plan de mejoramiento asignado a {llamado.aprendiz.first_name}.")
            return redirect('detalle_llamado', pk=llamado.id)
    else:
        form = PlanMejoramientoForm()
        
    context = {
        'titulo': 'Asignar Plan de Mejoramiento',
        'llamado': llamado,
        'form': form,
        'breadcrumbs': [
            {'nombre': 'Llamados', 'url': '/llamados/'},
            {'nombre': 'Detalle', 'url': f'/llamados/detalle/{llamado.id}/'},
            {'nombre': 'Nuevo Plan', 'url': ''}
        ]
    }
    return render(request, 'llamados/plan_form.html', context)

def editar_plan(request, plan_id):
    """Vista para actualizar el estado o fechas de un plan de mejoramiento existente"""
    plan = get_object_or_404(PlanMejoramiento, pk=plan_id)
    llamado = plan.llamado # Recuperamos el llamado asociado para la interfaz
    
    if request.method == 'POST':
        form = PlanMejoramientoForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, f"El estado del Plan de Mejoramiento ha sido actualizado a: {plan.get_estado_display()}.")
            return redirect('detalle_llamado', pk=llamado.id)
    else:
        form = PlanMejoramientoForm(instance=plan)
        
    context = {
        'titulo': 'Actualizar Plan de Mejoramiento',
        'llamado': llamado,
        'form': form,
        'breadcrumbs': [
            {'nombre': 'Llamados', 'url': '/llamados/'},
            {'nombre': 'Detalle', 'url': f'/llamados/detalle/{llamado.id}/'},
            {'nombre': 'Editar Plan', 'url': ''}
        ]
    }
    # Reutilizamos exactamente el mismo HTML que usamos para crearlo
    return render(request, 'llamados/plan_form.html', context)

def detalle_llamado(request, pk):
    """Vista para ver el expediente completo de un llamado y su plan de mejora"""
    # Buscamos el llamado específico usando su ID (Primary Key)
    llamado = get_object_or_404(LlamadoAtencion, pk=pk)
    
    # Verificamos si ya tiene un plan de mejoramiento asociado
    plan = None
    if hasattr(llamado, 'plan_mejoramiento'):
        plan = llamado.plan_mejoramiento
        
    context = {
        'titulo': 'Expediente Disciplinario',
        'llamado': llamado,
        'plan': plan,
        'breadcrumbs': [
            {'nombre': 'Llamados', 'url': '/llamados/'},
            {'nombre': 'Detalle del Caso', 'url': ''}
        ]
    }
    return render(request, 'llamados/detalle.html', context)

def estrategias(request):
    """Vista para listar y crear el catálogo de estrategias pedagógicas"""
    
    # Procesamiento real con ModelForm
    if request.method == 'POST':
        form = EstrategiaPedagogicaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Estrategia pedagógica creada correctamente.")
            return redirect('estrategias')
        else:
            messages.error(request, "Error al crear la estrategia. Revisa los datos.")
    else:
        form = EstrategiaPedagogicaForm()

    # Traemos los datos reales de la base de datos
    lista_estrategias = EstrategiaPedagogica.objects.all().order_by('-id')
    
    context = {
        'estrategias': lista_estrategias,
        'form': form,
        'breadcrumbs': [
            {'nombre': 'Llamados', 'url': '/llamados/'},
            {'nombre': 'Estrategias', 'url': ''}
        ]
    }
    return render(request, 'llamados/estrategias.html', context)

def editar_estrategia(request, pk):
    """Vista para editar una estrategia pedagógica existente"""
    estrategia = get_object_or_404(EstrategiaPedagogica, pk=pk)
    
    if request.method == 'POST':
        estrategia.nombre = request.POST.get('nombre')
        estrategia.descripcion = request.POST.get('descripcion')
        estrategia.plazo_dias = request.POST.get('plazo_dias')
        estrategia.save()
        
        messages.success(request, "La estrategia pedagógica fue actualizada correctamente.")
        return redirect('estrategias')

    context = {
        'titulo': 'Editar Estrategia',
        'estrategia': estrategia,
        'breadcrumbs': [
            {'nombre': 'Llamados', 'url': '/llamados/'},
            {'nombre': 'Estrategias', 'url': '/llamados/estrategias/'},
            {'nombre': 'Editar', 'url': ''}
        ]
    }
    return render(request, 'llamados/estrategia_form.html', context)

def eliminar_estrategia(request, pk):
    """Vista para eliminar una estrategia (Solo por POST por seguridad)"""
    estrategia = get_object_or_404(EstrategiaPedagogica, pk=pk)
    
    if request.method == 'POST':
        estrategia.delete()
        messages.success(request, "Estrategia eliminada del catálogo.")
        
    return redirect('estrategias')

def estadisticas(request):
    """Vista para el Dashboard de métricas disciplinarias (100% Dinámico)"""
    ficha_id = request.session.get('ficha_activa_id')
    
    if not ficha_id:
        messages.warning(request, "Selecciona una ficha para ver sus estadísticas.")
        return redirect('listar_llamados')
        
    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)
    
    # 1. Cálculos básicos para las tarjetas superiores
    llamados_ficha = LlamadoAtencion.objects.filter(ficha=ficha)
    total_casos = llamados_ficha.count()
    total_academicas = llamados_ficha.filter(tipo_falta='Academica').count()
    total_disciplinarias = llamados_ficha.filter(tipo_falta='Disciplinaria').count()
    pct_academicas = int((total_academicas / total_casos) * 100) if total_casos > 0 else 0
    pct_disciplinarias = int((total_disciplinarias / total_casos) * 100) if total_casos > 0 else 0
    verbales = llamados_ficha.filter(instancia='Verbal').count()
    escritos = llamados_ficha.filter(instancia='Escrito').count()
    comite = llamados_ficha.filter(instancia='Comite').count()

    # 2. Efectividad de Planes de Mejora (Porcentajes Reales)
    planes = PlanMejoramiento.objects.filter(llamado__ficha=ficha)
    total_planes = planes.count()
    planes_cerrados = planes.filter(estado='Cumplido').count()
    planes_riesgo = planes.filter(estado__in=['Incumplido', 'En Curso']).count()

    pct_cerrados = int((planes_cerrados / total_planes) * 100) if total_planes > 0 else 0
    pct_riesgo = int((planes_riesgo / total_planes) * 100) if total_planes > 0 else 0

    # 3. Alerta de Reincidencia (Top de aprendices con más de 1 caso)
    # Agrupamos por aprendiz y contamos cuántos llamados de cada tipo tienen
    reincidentes = llamados_ficha.values(
        'aprendiz__id',
        'aprendiz__first_name',
        'aprendiz__last_name',
        'aprendiz__documento' # <--- Corregido
    ).annotate(
        total=Count('id'),
        cant_verbales=Count('id', filter=Q(instancia='Verbal')),
        cant_escritos=Count('id', filter=Q(instancia='Escrito')),
        cant_comite=Count('id', filter=Q(instancia='Comite'))
    ).filter(total__gt=1).order_by('-total')[:5] # Solo los que tienen más de 1 caso, top 5

    context = {
        'ficha_activa': ficha,
        
        # Datos Tarjetas Superiores
        'total_casos': total_casos,
        'verbales': verbales,
        'escritos': escritos,
        'comite': comite,
        
        # Datos Gráficas (Análisis de Cumplimiento)
        'pct_academicas': pct_academicas,
        'pct_disciplinarias': pct_disciplinarias,
        
        # Datos Gráficas (Efectividad de Planes)
        'pct_cerrados': pct_cerrados,
        'pct_riesgo': pct_riesgo,
        
        # Datos Reincidencia
        'reincidentes': reincidentes,
        
        'breadcrumbs': [
            {'nombre': 'Llamados', 'url': '/llamados/'},
            {'nombre': 'Estadísticas', 'url': ''}
        ]
    }
    return render(request, 'llamados/estadisticas.html', context)