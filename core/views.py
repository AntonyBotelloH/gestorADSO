from django.shortcuts import render
from django.urls import reverse

from pendientes.models import Pendiente
from proyectos.models import Proyecto

def inicio(request):
    """Vista del Panel de Control principal (Dashboard) conectado a la BD."""
    
    # ==========================================
    # 1. PROYECTOS Y SPRINTS (DATOS REALES)
    # ==========================================
    proyectos_bd = Proyecto.objects.all().order_by('-fecha_inicio')[:5]
    sprints_reales = []
    
    for p in proyectos_bd:
        # Asignamos el color de Bootstrap según el estado real de la base de datos
        color = 'success' if p.estado == 'Al Día' else 'danger' if p.estado == 'Atrasado' else 'warning'
        sprints_reales.append({
            'proyecto': p.nombre,
            'sprint_nombre': 'En curso', # Más adelante lo cruzamos con el modelo de Sprints si lo creas
            'estado': p.estado,
            'color': color
        })

    # ==========================================
    # 2. TAREAS DEL INSTRUCTOR (DATOS REALES)
    # ==========================================
    # CORREGIDO: Trae todas las tareas, ordenadas para que las completadas salgan al final
    # Cambiamos '-creada_en' por '-creado_en'
    tareas_reales = Pendiente.objects.all().order_by('completada', '-creado_en')

    # ==========================================
    # 3. QUÓRUM, FONDOS Y ALERTAS (LÓGICA PREPARADA)
    # ==========================================
    # Aquí es donde conectaremos las otras apps apenas creemos sus models.py. 
    # Por ahora enviamos las variables en 0 para que no estalle el HTML.
    
    ''' LÓGICA REAL (A descomentar después)
    # Quórum
    total_aprendices = Usuario.objects.filter(rol='Aprendiz', ficha__codigo_ficha='3196477').count()
    asistentes_hoy = RegistroAsistencia.objects.filter(fecha=timezone.now().date(), asistio=True).count()
    porcentaje_asistencia = int((asistentes_hoy / total_aprendices) * 100) if total_aprendices > 0 else 0
    
    # Fondos
    fondo_actual = FondoFicha.objects.first()
    recaudado = fondo_actual.recaudado if fondo_actual else 0
    meta = fondo_actual.meta_dinero if fondo_actual else 1
    porcentaje_fondo = int((recaudado / meta) * 100)
    
    # Alertas
    alertas_pendientes = LlamadoAtencion.objects.filter(estado='Abierto').count()
    ultimas_alertas = LlamadoAtencion.objects.filter(estado='Abierto').order_by('-fecha')[:3]
    '''

    context = {
        'titulo': 'Inicio',
        'breadcrumbs': [{'nombre': 'Inicio', 'url': ''}],
        
        # Datos Reales
        'sprints': sprints_reales,
        'tareas': tareas_reales,
        
        # Datos en espera de sus modelos
        'quorum_presentes': 0, # Cambiar a: asistentes_hoy
        'quorum_total': 32,    # Cambiar a: total_aprendices
        'quorum_porcentaje': 0,# Cambiar a: porcentaje_asistencia
        'fondo_actual': '0',   # Cambiar a: recaudado
        'fondo_porcentaje': 0, # Cambiar a: porcentaje_fondo
        'alertas_pendientes':0,# Cambiar a: alertas_pendientes
        'alertas': [],         # Cambiar a: ultimas_alertas
    }
    
    return render(request, 'index.html', context)

def configuraciones(request):
    """Vista para la página de Ajustes y Accesibilidad."""
    context = {
        'titulo': 'Configuraciones',
        'breadcrumbs': [
            {'nombre': 'Configuraciones', 'url': ''}
        ]
    }
    return render(request, 'configuraciones.html', context)