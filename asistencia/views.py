import os
import glob
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required

from usuarios.decorators import rol_requerido 
from .models import SesionClase, RegistroAsistencia
from usuarios.models import Ficha, Usuario
from . import sofia_helpers

@login_required
@rol_requerido('VOCERO', 'INSTRUCTOR', 'ADMIN')
def inicio_asistencia(request):
    """Vista para registrar la asistencia del día o editar una sesión pasada."""
    ficha_id = request.session.get('ficha_activa_id')
    
    if not ficha_id:
        messages.warning(request, "Selecciona una ficha para tomar asistencia.")
        return redirect('inicio')

    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)
    aprendices = Usuario.objects.filter(ficha=ficha, rol__in=['APRENDIZ', 'VOCERO']).order_by('last_name')

    sesion_id = request.GET.get('sesion_id')
    
    if sesion_id:
        # Si venimos del historial a editar una sesión específica
        sesion = get_object_or_404(SesionClase, id=sesion_id, ficha=ficha)
    else:
        # 1. Obtenemos la fecha exacta de HOY en nuestra zona horaria local
        hoy = timezone.localtime(timezone.now()).date()
        
        # 2. Buscamos explícitamente si ya hay una clase registrada hoy
        sesion = SesionClase.objects.filter(ficha=ficha, fecha=hoy).first()
        
        # 3. Solo si NO existe ninguna, la creamos
        if not sesion:
            sesion = SesionClase.objects.create(ficha=ficha, fecha=hoy)

    if request.method == 'POST':
        # Protección: Si la sesión está cerrada, rechazamos los cambios
        if sesion.cerrada:
            messages.error(request, "Esta sesión ya se encuentra cerrada y no permite modificaciones.")
            return redirect('historial_asistencia')
            
        sesion.tema_tratado = request.POST.get('tema_tratado', '')
        sesion.save()

        # 1. Traemos TODOS los registros existentes de esta sesión de un solo golpe
        registros_existentes = RegistroAsistencia.objects.filter(sesion=sesion)
        dict_registros_bd = {reg.aprendiz_id: reg for reg in registros_existentes}

        registros_a_crear = []
        registros_a_actualizar = []

        # 2. Preparamos las listas en memoria
        for aprendiz in aprendices:
            estado = request.POST.get(f'estado_{aprendiz.id}', 'Presente')
            comentario = request.POST.get(f'comentario_{aprendiz.id}', '')
            
            if aprendiz.id in dict_registros_bd:
                registro = dict_registros_bd[aprendiz.id]
                if registro.estado != estado or registro.comentario != comentario:
                    registro.estado = estado
                    registro.comentario = comentario
                    registros_a_actualizar.append(registro)
            else:
                nuevo_registro = RegistroAsistencia(
                    sesion=sesion, 
                    aprendiz=aprendiz, 
                    estado=estado, 
                    comentario=comentario
                )
                registros_a_crear.append(nuevo_registro)

        # 3. Guardado en bloque ultrarrápido
        if registros_a_actualizar:
            RegistroAsistencia.objects.bulk_update(registros_a_actualizar, ['estado', 'comentario'])
            
        if registros_a_crear:
            RegistroAsistencia.objects.bulk_create(registros_a_crear)
        
        messages.success(request, "¡Asistencia guardada correctamente!")
        if sesion_id:
            return redirect('historial_asistencia')
        return redirect('historial_asistencia')

    # --- ESTA ES LA PARTE QUE FALTABA PARA QUE LA PÁGINA RENDERICE BIEN ---
    registros_hoy = RegistroAsistencia.objects.filter(sesion=sesion)
    # Usamos aprendiz_id por seguridad
    dict_registros = {reg.aprendiz_id: reg for reg in registros_hoy}

    # Inyectamos el registro actual directamente en el objeto aprendiz
    for aprendiz in aprendices:
        aprendiz.registro_actual = dict_registros.get(aprendiz.id)

    sesion_anterior = SesionClase.objects.filter(ficha=ficha, fecha__lt=sesion.fecha).order_by('-fecha').first()
    sesion_siguiente = SesionClase.objects.filter(ficha=ficha, fecha__gt=sesion.fecha).order_by('fecha').first()

    contexto = {
        'sesion': sesion,
        'sesion_anterior': sesion_anterior,
        'sesion_siguiente': sesion_siguiente,
        'aprendices': aprendices, # Ahora cada aprendiz trae su .registro_actual pegado
        'breadcrumbs': [
            {'nombre': 'Asistencia', 'url': '/asistencia/'},
            {'nombre': 'Toma de Asistencia', 'url': ''}
        ]
    }
    return render(request, 'asistencia/asistencia.html', contexto)

@login_required
@rol_requerido('VOCERO', 'INSTRUCTOR', 'ADMIN')
def historial_asistencias(request):
    """Vista para consultar sesiones anteriores con filtros de fecha."""
    ficha_id = request.session.get('ficha_activa_id')
    
    if not ficha_id:
        messages.warning(request, "Selecciona una ficha para ver el historial.")
        return redirect('inicio')

    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)
    
    # CORRECCIÓN 1: Contar solo el quórum de esta ficha específica (Aprendices + Vocero)
    total_aprendices = Usuario.objects.filter(
        ficha=ficha, 
        rol__in=['APRENDIZ', 'VOCERO']
    ).count()

    # CORRECCIÓN 2: Agregar total_excusas al annotate
    sesiones = SesionClase.objects.filter(ficha=ficha).annotate(
        total_presentes=Count('registros', filter=Q(registros__estado='Presente')),
        total_retardos=Count('registros', filter=Q(registros__estado='Retardo')),
        total_fallas=Count('registros', filter=Q(registros__estado='Falla')),
        total_excusas=Count('registros', filter=Q(registros__estado='Excusa')) # <--- Aquí está la magia
    ).order_by('-fecha')

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Filtro por defecto: Últimos 8 días si no hay filtro activo
    if not fecha_inicio and not fecha_fin:
        hoy = timezone.localtime(timezone.now()).date()
        hace_8_dias = hoy - timedelta(days=8)
        fecha_inicio = hace_8_dias.strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')

    if fecha_inicio:
        sesiones = sesiones.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        sesiones = sesiones.filter(fecha__lte=fecha_fin)

    contexto = {
        'sesiones': sesiones,
        'total_aprendices': total_aprendices,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'breadcrumbs': [
            {'nombre': 'Asistencia', 'url': '/asistencia/'},
            {'nombre': 'Historial', 'url': ''}
        ]
    }
    return render(request, 'asistencia/historial.html', contexto)
@login_required
@rol_requerido('VOCERO', 'INSTRUCTOR', 'ADMIN')
def estadisticas_asistencia(request):
    """Vista para el dashboard de rendimiento y riesgo de deserción."""
    ficha_id = request.session.get('ficha_activa_id')
    
    if not ficha_id:
        messages.warning(request, "Selecciona una ficha para ver las estadísticas.")
        return redirect('inicio')

    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)
    total_sesiones = SesionClase.objects.filter(ficha=ficha, cerrada=True).count()
    
    # CORRECCIÓN 1: Filtrar estrictamente por la ficha seleccionada y agregar al VOCERO
    aprendices = Usuario.objects.filter(
        ficha=ficha,
        rol__in=['APRENDIZ', 'VOCERO']
    ).annotate(
        total_fallas=Count('registroasistencia', filter=Q(registroasistencia__estado='Falla', registroasistencia__sesion__ficha=ficha, registroasistencia__sesion__cerrada=True)),
        total_retardos=Count('registroasistencia', filter=Q(registroasistencia__estado='Retardo', registroasistencia__sesion__ficha=ficha, registroasistencia__sesion__cerrada=True)),
        total_excusas=Count('registroasistencia', filter=Q(registroasistencia__estado='Excusa', registroasistencia__sesion__ficha=ficha, registroasistencia__sesion__cerrada=True))
    )

    aprendices_riesgo = 0
    retardos_totales = sum(a.total_retardos for a in aprendices)
    excusas_totales = sum(a.total_excusas for a in aprendices) # <-- NUEVO

    for aprendiz in aprendices:
        if total_sesiones > 0:
            aprendiz.porcentaje_falla = (aprendiz.total_fallas / total_sesiones) * 100
        else:
            aprendiz.porcentaje_falla = 0
            
        # Alerta crítica a partir de 5 fallas (Riesgo de Deserción)
        if aprendiz.total_fallas >= 5:
            aprendices_riesgo += 1

    # Detectar si el usuario quiere ver todas las fallas o todos los retardos
    mostrar_todas_fallas = request.GET.get('mostrar_todas_fallas') == '1'
    mostrar_todos_retardos = request.GET.get('mostrar_todos_retardos') == '1'

    limite_alertas_fallas = 0 if mostrar_todas_fallas else 2
    limite_alertas_retardos = 0 if mostrar_todos_retardos else 2

    aprendices_con_fallas = [a for a in aprendices if a.total_fallas > limite_alertas_fallas]
    aprendices_fallas_ordenados = sorted(aprendices_con_fallas, key=lambda x: x.total_fallas, reverse=True)

    aprendices_con_retardos = [a for a in aprendices if a.total_retardos > limite_alertas_retardos]
    aprendices_retardos_ordenados = sorted(aprendices_con_retardos, key=lambda x: x.total_retardos, reverse=True)

    total_registros = RegistroAsistencia.objects.filter(sesion__ficha=ficha, sesion__cerrada=True).count()
    
    # CORRECCIÓN 2: Inicializar y calcular también el porcentaje de Excusas
    pct_asistencia = pct_falla = pct_retardo = pct_excusa = 0
    
    if total_registros > 0:
        asistencias = RegistroAsistencia.objects.filter(sesion__ficha=ficha, sesion__cerrada=True, estado='Presente').count()
        fallas = RegistroAsistencia.objects.filter(sesion__ficha=ficha, sesion__cerrada=True, estado='Falla').count()
        retardos = RegistroAsistencia.objects.filter(sesion__ficha=ficha, sesion__cerrada=True, estado='Retardo').count()
        excusas = RegistroAsistencia.objects.filter(sesion__ficha=ficha, sesion__cerrada=True, estado='Excusa').count()
        
        pct_asistencia = (asistencias / total_registros) * 100
        pct_falla = (fallas / total_registros) * 100
        pct_retardo = (retardos / total_registros) * 100
        pct_excusa = (excusas / total_registros) * 100

    contexto = {
        'total_sesiones': total_sesiones,
        'aprendices_riesgo': aprendices_riesgo,
        'retardos_totales': retardos_totales,
        'excusas_totales': excusas_totales,
        'pct_asistencia': pct_asistencia,
        'pct_falla': pct_falla,
        'pct_retardo': pct_retardo,
        'pct_excusa': pct_excusa,
        'aprendices_fallas': aprendices_fallas_ordenados,
        'aprendices_retardos': aprendices_retardos_ordenados,
        'mostrar_todas_fallas': mostrar_todas_fallas,
        'mostrar_todos_retardos': mostrar_todos_retardos,
        'breadcrumbs': [
            {'nombre': 'Asistencia', 'url': '/asistencia/'},
            {'nombre': 'Análisis Estadístico', 'url': ''}
        ]
    }
    
    return render(request, 'asistencia/estadisticas.html', contexto)

@login_required
@rol_requerido('VOCERO', 'INSTRUCTOR', 'ADMIN')
def justificar_falla(request, registro_id):
    """Permite cambiar el estado de una asistencia de Falla a Excusa directamente desde el reporte."""
    if request.method == 'POST':
        registro = get_object_or_404(RegistroAsistencia, id=registro_id)
        
        if registro.sesion.cerrada:
            messages.error(request, "No se puede justificar esta falla porque la sesión de clase ya se encuentra cerrada.")
            return redirect(request.META.get('HTTP_REFERER', 'inicio'))
            
        if registro.estado in ['Falla', 'Retardo']:
            registro.estado = 'Excusa'
            registro.save()
            messages.success(request, f"El registro de {registro.aprendiz.first_name} ha sido justificado (Convertido a Excusa).")
        # Nos redirige sutilmente de vuelta al informe donde estábamos
        return redirect(request.META.get('HTTP_REFERER', 'inicio'))
    return redirect('inicio')

@login_required
@rol_requerido('VOCERO', 'INSTRUCTOR', 'ADMIN')
def cerrar_sesion(request, sesion_id):
    """Bloquea una sesión de clase para evitar futuras ediciones."""
    if request.method == 'POST':
        sesion = get_object_or_404(SesionClase, id=sesion_id)
        sesion.cerrada = True
        sesion.save()
        messages.success(request, f"La sesión de asistencia del {sesion.fecha} ha sido cerrada de forma definitiva.")
    return redirect('historial_asistencia')

@login_required
@rol_requerido('VOCERO', 'INSTRUCTOR', 'ADMIN')
def detalle_sesion(request, sesion_id):
    """Muestra el detalle de asistencia de un día en específico (Fallas, Excusas y Retardos)."""
    ficha_id = request.session.get('ficha_activa_id')
    if not ficha_id:
        return redirect('inicio')
        
    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)
    sesion = get_object_or_404(SesionClase, id=sesion_id, ficha=ficha)
    
    # 0. Sesiones anterior y siguiente para navegación
    sesion_anterior = SesionClase.objects.filter(
        ficha=ficha, 
        fecha__lt=sesion.fecha
    ).order_by('-fecha').first()
    
    sesion_siguiente = SesionClase.objects.filter(
        ficha=ficha, 
        fecha__gt=sesion.fecha
    ).order_by('fecha').first()
    
    # 1. Inasistencias (Fallas y Excusas)
    inasistencias = RegistroAsistencia.objects.filter(
        sesion=sesion,
        estado__in=['Falla', 'Excusa']
    ).select_related('aprendiz').order_by('aprendiz__last_name', 'aprendiz__first_name')
    
    # 2. Retardos
    retardos = RegistroAsistencia.objects.filter(
        sesion=sesion,
        estado='Retardo'
    ).select_related('aprendiz').order_by('aprendiz__last_name', 'aprendiz__first_name')
    
    contexto = {
        'sesion': sesion,
        'sesion_anterior': sesion_anterior,
        'sesion_siguiente': sesion_siguiente,
        'inasistencias': inasistencias,
        'retardos': retardos,
        'prueba_sincronizacion': request.session.get('prueba_sincronizacion'),
        'error_sincronizacion': request.session.get('error_sincronizacion'),
        'breadcrumbs': [
            {'nombre': 'Asistencia', 'url': '/asistencia/'},
            {'nombre': 'Historial', 'url': '/asistencia/historial/'}, # Ajusta la URL si es diferente
            {'nombre': f'Detalle {sesion.fecha}', 'url': ''}
        ]
    }
    
    if 'prueba_sincronizacion' in request.session: del request.session['prueba_sincronizacion']
    if 'error_sincronizacion' in request.session: del request.session['error_sincronizacion']
    
    return render(request, 'asistencia/detalle_sesion.html', contexto)

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def registro_sofia(request):
    """Dashboard para controlar paso a paso la automatización con SOFIA Plus."""
    if request.method == 'POST':
        doc = request.POST.get('aprendiz_documento')
        if doc:
            request.session['aprendiz_prueba_doc'] = str(doc)
            messages.success(request, "Aprendiz para pruebas seleccionado correctamente.")
        return redirect('registro_sofia')

    ficha_id = request.session.get('ficha_activa_id')
    aprendices = []
    if ficha_id:
        ficha = Ficha.objects.filter(codigo_ficha=ficha_id).first()
        if ficha:
            aprendices = Usuario.objects.filter(ficha=ficha, rol__in=['APRENDIZ', 'VOCERO']).order_by('first_name', 'last_name')

    contexto = {
        'titulo': 'Test de Sincronización SOFIA Plus',
        'breadcrumbs': [
            {'nombre': 'Configuración', 'url': '#'},
            {'nombre': 'Test Sincronización', 'url': ''}
        ],
        'aprendices': aprendices,
        'prueba_conexion': request.session.get('prueba_conexion_sofia'),
        'prueba_rol': request.session.get('prueba_rol_sofia'),
        'prueba_navegacion': request.session.get('prueba_navegacion_sofia'),
        'error_conexion': request.session.get('error_conexion_sofia'),
        'error_rol': request.session.get('error_rol_sofia'),
        'error_navegacion': request.session.get('error_navegacion_sofia'),
        'prueba_seleccion': request.session.get('prueba_seleccion_sofia'),
        'error_seleccion': request.session.get('error_seleccion_sofia'),
        'prueba_seleccion_aprendiz': request.session.get('prueba_seleccion_aprendiz_sofia'),
        'error_seleccion_aprendiz': request.session.get('error_seleccion_aprendiz_sofia'),
        'prueba_consulta': request.session.get('prueba_consulta_sofia'),
        'error_consulta': request.session.get('error_consulta_sofia'),
    }

    sofia_helpers.clear_session_keys(request, [
        'error_conexion_sofia',
        'error_rol_sofia',
        'error_navegacion_sofia',
        'error_seleccion_sofia',
        'error_seleccion_aprendiz_sofia',
        'error_consulta_sofia',
    ])

    return render(request, 'asistencia/registro_sofia.html', contexto)

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def probar_conexion_sofia(request):
    """Inicia un navegador en segundo plano, intenta cargar SOFIA y toma una captura."""
    credencial = getattr(request.user, 'credenciales_sofia', None)
    if not sofia_helpers.validate_sofia_credencial(request, credencial, 'error_conexion_sofia', "No tienes credenciales configuradas en Configuración > SOFIA Plus."):
        return redirect('registro_sofia')

    def action(driver):
        sofia_helpers.login_sofia(driver, credencial)
        time.sleep(5)

    sofia_helpers.run_sofia_action(
        request,
        credencial,
        action,
        'prueba_conexion_sofia',
        'conexion.png',
        error_session_key='error_conexion_sofia',
        error_proof_name='error_conexion.png',
        success_message="Prueba de conexión a SOFIA Plus ejecutada."
    )

    return redirect('registro_sofia')

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def purgar_imagenes_prueba(request):
    """Elimina las imágenes de prueba generadas y limpia la sesión."""
    proofs_dir = os.path.join(settings.MEDIA_ROOT, 'sofia_proofs')
    
    if os.path.exists(proofs_dir):
        for file_path in glob.glob(os.path.join(proofs_dir, '*.png')):
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                    
    keys_to_clear = [
        'prueba_conexion_sofia', 'prueba_rol_sofia', 'prueba_navegacion_sofia',
        'prueba_seleccion_sofia', 'prueba_seleccion_aprendiz_sofia', 'prueba_consulta_sofia',
    ]
    sofia_helpers.clear_session_keys(request, keys_to_clear)
    
    messages.success(request, "Las imágenes de prueba han sido purgadas exitosamente.")
    return redirect('registro_sofia')

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def probar_consulta_inasistencia_sofia(request):
    """Sexto paso: Ejecuta la consulta de inasistencias y toma un pantallazo de la tabla de resultados."""
    credencial = getattr(request.user, 'credenciales_sofia', None)
    ficha_id = request.session.get('ficha_activa_id')
    documento_prueba = request.session.get('aprendiz_prueba_doc')

    if not documento_prueba:
        request.session['error_consulta_sofia'] = 'Selecciona un aprendiz para la prueba en la parte superior.'
        return redirect('registro_sofia')

    if not credencial or not credencial.get_password():
        request.session['error_consulta_sofia'] = 'No tienes credenciales configuradas.'
        return redirect('registro_sofia')

    if not ficha_id:
        request.session['error_consulta_sofia'] = 'Selecciona una ficha en el menú lateral.'
        return redirect('registro_sofia')

    sofia_helpers.run_sofia_action(
        request,
        credencial,
        lambda driver: sofia_helpers.prepare_consultar_inasistencias(driver, credencial, ficha_id, documento_prueba),
        'prueba_consulta_sofia',
        'consulta_inasistencia.png',
        error_session_key='error_consulta_sofia',
        error_proof_name='error_consulta.png',
        success_message='Se consultaron correctamente las inasistencias del aprendiz.'
    )

    return redirect('registro_sofia')

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def consultar_inasistencias_sofia(request, usuario_id):
    """Consulta inasistencias en SOFIA para un aprendiz y guarda la foto temporal en sesión."""
    aprendiz = get_object_or_404(Usuario, id=usuario_id)
    ficha_id = request.session.get('ficha_activa_id')

    request.session['prueba_consulta_sofia_aprendiz'] = str(aprendiz.id)
    request.session.pop('img_consulta_sofia', None)
    request.session.pop('error_consulta_sofia_aprendiz', None)
    request.session.pop('msg_error_consulta_sofia', None)

    credencial = getattr(request.user, 'credenciales_sofia', None)
    documento_prueba = aprendiz.documento

    if not credencial or not credencial.get_password():
        request.session['error_consulta_sofia_aprendiz'] = str(aprendiz.id)
        request.session['msg_error_consulta_sofia'] = 'No tienes credenciales configuradas.'
        return redirect('informe_aprendiz', usuario_id=aprendiz.id)

    if not ficha_id:
        request.session['error_consulta_sofia_aprendiz'] = str(aprendiz.id)
        request.session['msg_error_consulta_sofia'] = 'Selecciona una ficha en el menú lateral.'
        return redirect('informe_aprendiz', usuario_id=aprendiz.id)

    sofia_helpers.run_sofia_action(
        request,
        credencial,
        lambda driver: sofia_helpers.prepare_consultar_inasistencias(driver, credencial, ficha_id, documento_prueba),
        'img_consulta_sofia',
        f'consulta_{documento_prueba}.png',
        error_session_key='error_consulta_sofia_aprendiz',
        error_proof_name=f'error_consulta_{documento_prueba}.png',
        success_message=f'Reporte de SOFIA Plus generado para {aprendiz.first_name}.'
    )

    return redirect('informe_aprendiz', usuario_id=aprendiz.id)

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def sincronizar_falla_sofia(request, registro_id):
    """Extrae los datos de la base de datos y simula el registro de inasistencia en SOFIA."""
    registro = get_object_or_404(RegistroAsistencia, id=registro_id)
    sesion = registro.sesion

    if not sesion.cerrada:
        messages.error(request, 'La sesión debe estar cerrada para poder sincronizar fallas con SOFIA Plus.')
        return redirect(request.META.get('HTTP_REFERER', f'/asistencia/detalle_sesion/{sesion.id}/'))

    if registro.sincronizado_sofia:
        messages.info(request, 'Esta inasistencia ya se encuentra reportada en SOFIA Plus.')
        return redirect(request.META.get('HTTP_REFERER', f'/asistencia/detalle_sesion/{sesion.id}/'))

    credencial = getattr(request.user, 'credenciales_sofia', None)
    if not credencial or not credencial.get_password():
        request.session['error_sincronizacion'] = 'No tienes credenciales configuradas en SOFIA Plus.'
        return redirect(request.META.get('HTTP_REFERER', f'/asistencia/detalle_sesion/{sesion.id}/'))

    ficha_id = sesion.ficha.codigo_ficha
    documento_aprendiz = registro.aprendiz.documento
    fecha_str = sesion.fecha.strftime('%d/%m/%Y')
    horas_falla = '6'

    driver = None
    try:
        driver = sofia_helpers.create_sofia_driver()
        wait = sofia_helpers.prepare_registrar_inasistencia_aprendiz(driver, credencial, ficha_id, documento_aprendiz)

        btn_consultar = wait.until(sofia_helpers.EC.presence_of_element_located((sofia_helpers.By.XPATH, "//input[contains(@value, 'Consultar') or contains(@id, 'Consultar') or @type='submit']")))
        driver.execute_script('arguments[0].click();', btn_consultar)
        time.sleep(3)

        try:
            sofia_helpers.fill_inasistencia_form(driver, fecha_str, horas_falla)
            time.sleep(1)
            sofia_helpers.click_body(driver)
            time.sleep(1.5)
            sofia_helpers.hide_required_messages(driver)
            sofia_helpers.capture_form_state(driver, registro, documento_aprendiz, sesion)

            btn_guardar = driver.find_element(sofia_helpers.By.ID, 'formNovedadAprendiz:btnRegistrarNovedad')
            driver.execute_script('arguments[0].click();', btn_guardar)
            wait.until(sofia_helpers.EC.presence_of_element_located(
                (sofia_helpers.By.XPATH, "//span[contains(@class, 'info') and contains(text(), 'Registrada Correctamente')]")
            ))
            registro.sincronizado_sofia = True
            registro.save()
        except Exception:
            if not registro.captura_sofia:
                try:
                    sofia_helpers.capture_form_state(driver, registro, documento_aprendiz, sesion, suffix='error')
                except Exception:
                    pass

        if registro.sincronizado_sofia:
            messages.success(request, f'¡Éxito! La falla de {registro.aprendiz.first_name} se reportó correctamente en SOFIA Plus.')
        else:
            messages.warning(request, 'Los datos se ingresaron pero no se confirmó el registro en SOFIA Plus. Revisa la captura en el expediente.')
    except Exception as e:
        error_name = type(e).__name__
        error_msg = str(e).split('Stacktrace:')[0].strip()
        messages.error(request, f'El bot se detuvo ({error_name}). Detalles: {error_msg[:150]}')
    finally:
        if driver:
            sofia_helpers.quit_sofia_driver(driver)

    return redirect('detalle_registro', registro_id=registro.id)

@login_required
@rol_requerido('VOCERO', 'INSTRUCTOR', 'ADMIN')
def detalle_registro(request, registro_id):
    """Muestra el detalle individual de una asistencia y su evidencia fotográfica de SOFIA."""
    registro = get_object_or_404(RegistroAsistencia, id=registro_id)
    contexto = {
        'titulo': f'Detalle de Asistencia - {registro.aprendiz.get_full_name()}',
        'registro': registro,
        'breadcrumbs': [
            {'nombre': 'Asistencia', 'url': '/asistencia/'},
            {'nombre': f'Sesión {registro.sesion.fecha}', 'url': f'/asistencia/detalle_sesion/{registro.sesion.id}/'},
            {'nombre': 'Evidencia', 'url': ''}
        ]
    }
    return render(request, 'asistencia/detalle_registro.html', contexto)

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def probar_seleccion_aprendiz_sofia(request):
    """Quinto paso: Selecciona un aprendiz específico para la prueba."""
    credencial = getattr(request.user, 'credenciales_sofia', None)
    ficha_id = request.session.get('ficha_activa_id')
    documento_prueba = request.session.get('aprendiz_prueba_doc')

    if not documento_prueba:
        request.session['error_seleccion_aprendiz_sofia'] = 'Selecciona un aprendiz para la prueba en la parte superior.'
        return redirect('registro_sofia')

    if not sofia_helpers.validate_sofia_credencial(request, credencial, 'error_seleccion_aprendiz_sofia'):
        return redirect('registro_sofia')

    if not sofia_helpers.validate_ficha_id(request, ficha_id, 'error_seleccion_aprendiz_sofia'):
        return redirect('registro_sofia')

    sofia_helpers.run_sofia_action(
        request,
        credencial,
        lambda driver: sofia_helpers.prepare_registrar_inasistencia_aprendiz(driver, credencial, ficha_id, documento_prueba),
        'prueba_seleccion_aprendiz_sofia',
        'seleccion_aprendiz.png',
        error_session_key='error_seleccion_aprendiz_sofia',
        error_proof_name='error_seleccion_aprendiz.png',
        success_message=f'Se buscó correctamente el aprendiz con documento {documento_prueba}.'
    )

    return redirect('registro_sofia')

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def probar_seleccion_ficha_sofia(request):
    """Cuarto paso: Abre el popup de fichas y selecciona la ficha que el usuario tiene activa."""
    credencial = getattr(request.user, 'credenciales_sofia', None)
    ficha_id = request.session.get('ficha_activa_id')

    if not sofia_helpers.validate_sofia_credencial(request, credencial, 'error_seleccion_sofia'):
        return redirect('registro_sofia')

    if not sofia_helpers.validate_ficha_id(request, ficha_id, 'error_seleccion_sofia', 'Selecciona una ficha en el menú lateral de Gestor SENA para continuar.'):
        return redirect('registro_sofia')

    sofia_helpers.run_sofia_action(
        request,
        credencial,
        lambda driver: sofia_helpers.prepare_registrar_inasistencia(driver, credencial, ficha_id),
        'prueba_seleccion_sofia',
        'seleccion_ficha.png',
        error_session_key='error_seleccion_sofia',
        error_proof_name='error_seleccion_ficha.png',
        success_message=f'Se seleccionó exitosamente la ficha {ficha_id} en el formulario.'
    )

    return redirect('registro_sofia')

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def probar_navegacion_sofia(request):
    """Tercer paso: Navega por el menú hasta llegar al formulario de inasistencias."""
    credencial = getattr(request.user, 'credenciales_sofia', None)

    if not sofia_helpers.validate_sofia_credencial(request, credencial, 'error_navegacion_sofia'):
        return redirect('registro_sofia')

    sofia_helpers.run_sofia_action(
        request,
        credencial,
        lambda driver: sofia_helpers.navigate_to_registrar_inasistencia(driver, sofia_helpers.login_as_instructor(driver, credencial)),
        'prueba_navegacion_sofia',
        'navegacion.png',
        error_session_key='error_navegacion_sofia',
        error_proof_name='error_navegacion.png',
        success_message='Navegación hasta el formulario completada con éxito.'
    )

    return redirect('registro_sofia')

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def probar_rol_sofia(request):
    """Inicia el navegador, simula el cambio de rol y toma captura."""
    credencial = getattr(request.user, 'credenciales_sofia', None)

    if not sofia_helpers.validate_sofia_credencial(request, credencial, 'error_rol_sofia', 'No tienes credenciales configuradas en Configuración > SOFIA Plus.'):
        return redirect('registro_sofia')

    sofia_helpers.run_sofia_action(
        request,
        credencial,
        lambda driver: sofia_helpers.login_as_instructor(driver, credencial),
        'prueba_rol_sofia',
        'rol_instructor.png',
        error_session_key='error_rol_sofia',
        error_proof_name='error_rol.png',
        success_message='Prueba de cambio de rol ejecutada.'
    )

    return redirect('registro_sofia')
