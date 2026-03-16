from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required

from usuarios.decorators import rol_requerido 
from .models import SesionClase, RegistroAsistencia
from usuarios.models import Ficha, Usuario

@login_required
@rol_requerido('VOCERO', 'INSTRUCTOR', 'Admin')
def inicio_asistencia(request):
    """Vista para registrar la asistencia del día o editar una sesión pasada."""
    ficha_id = request.session.get('ficha_activa_id')
    
    if not ficha_id:
        messages.warning(request, "Selecciona una ficha para tomar asistencia.")
        return redirect('inicio')

    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)
    aprendices = Usuario.objects.filter(rol='APRENDIZ') 

    sesion_id = request.GET.get('sesion_id')
    
    if sesion_id:
        # Si venimos del historial a editar una sesión específica
        sesion = get_object_or_404(SesionClase, id=sesion_id, ficha=ficha)
    else:
        # LÓGICA CORREGIDA PARA EVITAR DUPLICADOS
        # 1. Obtenemos la fecha exacta de HOY en nuestra zona horaria local
        hoy = timezone.localtime(timezone.now()).date()
        
        # 2. Buscamos explícitamente si ya hay una clase registrada hoy
        sesion = SesionClase.objects.filter(ficha=ficha, fecha=hoy).first()
        
        # 3. Solo si NO existe ninguna, la creamos
        if not sesion:
            sesion = SesionClase.objects.create(ficha=ficha, fecha=hoy)

    if request.method == 'POST':
        sesion.tema_tratado = request.POST.get('tema_tratado', '')
        sesion.save()

        for aprendiz in aprendices:
            estado = request.POST.get(f'estado_{aprendiz.id}', 'Presente')
            comentario = request.POST.get(f'comentario_{aprendiz.id}', '')
            
            RegistroAsistencia.objects.update_or_create(
                sesion=sesion, 
                aprendiz=aprendiz,
                defaults={'estado': estado, 'comentario': comentario}
            )
        
        messages.success(request, "¡Asistencia guardada correctamente!")
        if sesion_id:
            return redirect(f"/asistencia/?sesion_id={sesion_id}")
        return redirect('inicio_asistencia')

    registros_hoy = RegistroAsistencia.objects.filter(sesion=sesion)
    dict_registros = {reg.aprendiz.id: reg for reg in registros_hoy}

    # Se eliminó la variable 'titulo' redundante
    contexto = {
        'sesion': sesion,
        'aprendices': aprendices,
        'dict_registros': dict_registros,
        'breadcrumbs': [
            {'nombre': 'Asistencia', 'url': '/asistencia/'},
            {'nombre': 'Toma de Asistencia', 'url': ''}
        ]
    }
    return render(request, 'asistencia/asistencia.html', contexto)


@login_required
@rol_requerido('VOCERO', 'INSTRUCTOR', 'Admin')
def historial_asistencias(request):
    """Vista para consultar sesiones anteriores con filtros de fecha."""
    ficha_id = request.session.get('ficha_activa_id')
    
    if not ficha_id:
        messages.warning(request, "Selecciona una ficha para ver el historial.")
        return redirect('inicio')

    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)
    total_aprendices = Usuario.objects.filter(rol='APRENDIZ').count()

    sesiones = SesionClase.objects.filter(ficha=ficha).annotate(
        total_presentes=Count('registros', filter=Q(registros__estado='Presente')),
        total_retardos=Count('registros', filter=Q(registros__estado='Retardo')),
        total_fallas=Count('registros', filter=Q(registros__estado='Falla'))
    ).order_by('-fecha')

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if fecha_inicio:
        sesiones = sesiones.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        sesiones = sesiones.filter(fecha__lte=fecha_fin)

    # Se eliminó la variable 'titulo' redundante
    contexto = {
        'sesiones': sesiones,
        'total_aprendices': total_aprendices,
        'breadcrumbs': [
            {'nombre': 'Asistencia', 'url': '/asistencia/'},
            {'nombre': 'Historial', 'url': ''}
        ]
    }
    return render(request, 'asistencia/historial.html', contexto)


@login_required
@rol_requerido('VOCERO', 'INSTRUCTOR', 'Admin')
def estadisticas_asistencia(request):
    """Vista para el dashboard de rendimiento y riesgo de deserción."""
    ficha_id = request.session.get('ficha_activa_id')
    
    if not ficha_id:
        messages.warning(request, "Selecciona una ficha para ver las estadísticas.")
        return redirect('inicio')

    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)
    total_sesiones = SesionClase.objects.filter(ficha=ficha).count()
    
    aprendices = Usuario.objects.filter(rol='APRENDIZ').annotate(
        total_fallas=Count('registroasistencia', filter=Q(registroasistencia__estado='Falla', registroasistencia__sesion__ficha=ficha)),
        total_retardos=Count('registroasistencia', filter=Q(registroasistencia__estado='Retardo', registroasistencia__sesion__ficha=ficha)),
        total_excusas=Count('registroasistencia', filter=Q(registroasistencia__estado='Excusa', registroasistencia__sesion__ficha=ficha))
    )

    aprendices_riesgo = 0
    retardos_totales = sum(a.total_retardos for a in aprendices)

    for aprendiz in aprendices:
        if total_sesiones > 0:
            aprendiz.porcentaje_falla = (aprendiz.total_fallas / total_sesiones) * 100
        else:
            aprendiz.porcentaje_falla = 0
            
        if aprendiz.total_fallas >= 5:
            aprendices_riesgo += 1

    aprendices_con_fallas = [a for a in aprendices if a.total_fallas > 0]
    aprendices_ordenados = sorted(aprendices_con_fallas, key=lambda x: x.total_fallas, reverse=True)

    total_registros = RegistroAsistencia.objects.filter(sesion__ficha=ficha).count()
    pct_asistencia = pct_falla = pct_retardo = 0
    
    if total_registros > 0:
        asistencias = RegistroAsistencia.objects.filter(sesion__ficha=ficha, estado='Presente').count()
        fallas = RegistroAsistencia.objects.filter(sesion__ficha=ficha, estado='Falla').count()
        retardos = RegistroAsistencia.objects.filter(sesion__ficha=ficha, estado='Retardo').count()
        
        pct_asistencia = (asistencias / total_registros) * 100
        pct_falla = (fallas / total_registros) * 100
        pct_retardo = (retardos / total_registros) * 100

    # Se eliminó la variable 'titulo' redundante
    contexto = {
        'total_sesiones': total_sesiones,
        'aprendices_riesgo': aprendices_riesgo,
        'retardos_totales': retardos_totales,
        'pct_asistencia': pct_asistencia,
        'pct_falla': pct_falla,
        'pct_retardo': pct_retardo,
        'aprendices': aprendices_ordenados,
        'breadcrumbs': [
            {'nombre': 'Asistencia', 'url': '/asistencia/'},
            {'nombre': 'Análisis Estadístico', 'url': ''}
        ]
    }
    
    return render(request, 'asistencia/estadisticas.html', contexto)