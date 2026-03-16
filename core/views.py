from django.shortcuts import redirect, render
from django.urls import reverse
from django.db.models import Q, Sum
from django.utils import timezone

# Importación de todos tus modelos
from pendientes.models import Pendiente
from usuarios.models import Usuario
from llamados.models import LlamadoAtencion
from proyectos.models import Proyecto
from asistencia.models import SesionClase, RegistroAsistencia
from fondos.models import Movimiento, MetaFinanciera

from django.contrib.auth.decorators import login_required

@login_required
def inicio(request):
    """Vista del Panel de Control principal (Dashboard) 100% Dinámico."""
    
    # 0. Sincronización con el Context Processor
    ficha_actual = request.session.get('ficha_activa_id')
    hoy = timezone.now().date()
    
    # 1. Inicialización de variables (KPIs)
    total_aprendices = 0
    asistentes_hoy = 0
    porcentaje_asistencia = 0
    saldo_fondo = 0
    porcentaje_fondo = 0
    nombre_meta = "Sin meta activa"
    alertas_pendientes = 0
    sprints_reales = []
    alertas_reales = []

    # ==========================================
    # 2. CONSULTAS FILTRADAS (Si hay ficha seleccionada)
    # ==========================================
    if ficha_actual and ficha_actual != 'general':
        
        # --- QUÓRUM (Asistencia) ---
        total_aprendices = Usuario.objects.filter(
            ficha__codigo_ficha=ficha_actual, 
            rol='APRENDIZ'
        ).count()

        sesion_hoy = SesionClase.objects.filter(ficha__codigo_ficha=ficha_actual, fecha=hoy).first()
        if sesion_hoy:
            asistentes_hoy = RegistroAsistencia.objects.filter(
                sesion=sesion_hoy, 
                estado__in=['Presente', 'Retardo']
            ).count()

        if total_aprendices > 0:
            porcentaje_asistencia = int((asistentes_hoy / total_aprendices) * 100)

        # --- FONDOS (Contabilidad Real) ---
        ingresos = Movimiento.objects.filter(
            ficha__codigo_ficha=ficha_actual, 
            concepto__tipo_operacion='Ingreso'
        ).aggregate(total=Sum('valor'))['total'] or 0

        egresos = Movimiento.objects.filter(
            ficha__codigo_ficha=ficha_actual, 
            concepto__tipo_operacion='Egreso'
        ).aggregate(total=Sum('valor'))['total'] or 0

        saldo_fondo = ingresos - egresos

        meta = MetaFinanciera.objects.filter(ficha__codigo_ficha=ficha_actual, activa=True).first()
        if meta:
            nombre_meta = meta.nombre
            if meta.valor_objetivo > 0:
                porcentaje_fondo = min(int((saldo_fondo / meta.valor_objetivo) * 100), 100)

        # --- PROYECTOS ---
        proyectos_bd = Proyecto.objects.filter(ficha__codigo_ficha=ficha_actual).order_by('-fecha_inicio')[:5]
        for p in proyectos_bd:
            color = 'success' if p.estado == 'Al Día' else 'danger' if p.estado == 'Atrasado' else 'warning'
            sprints_reales.append({
                'proyecto': p.nombre, 
                'sprint_nombre': 'En curso', 
                'estado': p.estado, 
                'color': color
            })

        # --- ALERTAS DISCIPLINARIAS ---
        alertas_pendientes = LlamadoAtencion.objects.filter(
            ficha__codigo_ficha=ficha_actual
        ).exclude(plan_mejora__estado='Cumplido').count()
        
        ultimos_llamados = LlamadoAtencion.objects.filter(
            ficha__codigo_ficha=ficha_actual
        ).order_by('-fecha_incidente')[:5]
        
        for llamado in ultimos_llamados:
            color = 'warning' if llamado.instancia == 'Escrito' else 'info' if llamado.instancia == 'Verbal' else 'dark'
            alertas_reales.append({
                'aprendiz': llamado.aprendiz.get_full_name(), 
                'tipo': llamado.get_instancia_display(), 
                'color': color
            })

    # ==========================================
    # 3. TAREAS (Ficha actual + Generales)
    # ==========================================
    if ficha_actual == 'general' or not ficha_actual:
        tareas_reales = Pendiente.objects.filter(ficha_vinculada__isnull=True).order_by('completada', '-creado_en')
    else:
        tareas_reales = Pendiente.objects.filter(
            Q(ficha_vinculada__codigo_ficha=ficha_actual) | Q(ficha_vinculada__isnull=True)
        ).order_by('completada', '-creado_en')

    # ==========================================
    # 4. CONSTRUCCIÓN DEL CONTEXTO
    # ==========================================
    context = {
        'titulo': 'Inicio',
        'breadcrumbs': [{'nombre': 'Inicio', 'url': ''}],
        
        'sprints': sprints_reales,
        'tareas': tareas_reales,
        'alertas': alertas_reales,
        
        # KPIs de la parte superior
        'alertas_pendientes': alertas_pendientes,
        'quorum_total': total_aprendices,
        'quorum_presentes': asistentes_hoy,
        'quorum_porcentaje': porcentaje_asistencia,
        'fondo_actual': f"{saldo_fondo:,.0f}",
        'fondo_porcentaje': porcentaje_fondo,
        'nombre_meta': nombre_meta,
    }
    
    return render(request, 'index.html', context)

def configuraciones(request):
    """Vista para Ajustes."""
    context = {
        'titulo': 'Configuraciones',
        'breadcrumbs': [{'nombre': 'Configuraciones', 'url': ''}]
    }
    return render(request, 'configuraciones.html', context)

def cambiar_ficha(request):
    """Lógica global de cambio de contexto de ficha."""
    if request.method == 'POST':
        codigo = request.POST.get('ficha_id')
        request.session['ficha_activa_id'] = None if codigo == 'general' else codigo
            
    return redirect(request.META.get('HTTP_REFERER', reverse('inicio')))