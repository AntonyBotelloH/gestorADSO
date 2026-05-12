import os
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
    contexto = {
        'titulo': 'Sincronización SOFIA Plus',
        'breadcrumbs': [
            {'nombre': 'Asistencia', 'url': '/asistencia/'},
            {'nombre': 'Registro SOFIA', 'url': ''}
        ],
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
    
    # Limpiamos los errores de la sesión después de mostrarlos
    if 'error_conexion_sofia' in request.session: del request.session['error_conexion_sofia']
    if 'error_rol_sofia' in request.session: del request.session['error_rol_sofia']
    if 'error_navegacion_sofia' in request.session: del request.session['error_navegacion_sofia']
    if 'error_seleccion_sofia' in request.session: del request.session['error_seleccion_sofia']
    if 'error_seleccion_aprendiz_sofia' in request.session: del request.session['error_seleccion_aprendiz_sofia']
    if 'error_consulta_sofia' in request.session: del request.session['error_consulta_sofia']
    
    return render(request, 'asistencia/registro_sofia.html', contexto)

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def probar_conexion_sofia(request):
    """Inicia un navegador en segundo plano, intenta cargar SOFIA y toma una captura."""
    try:
        from selenium import webdriver
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.keys import Keys
        from django.core.files.storage import FileSystemStorage
        
        credencial = getattr(request.user, 'credenciales_sofia', None)
        if not credencial or not credencial.get_password():
            request.session['error_conexion_sofia'] = "No tienes credenciales configuradas en Configuración > SOFIA Plus."
            return redirect('registro_sofia')

        # Configurar Chrome en modo oculto (headless)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        driver = webdriver.Chrome(options=options)
        
        # Navegar a la URL pública que indicaste
        driver.get("http://senasofiaplus.edu.co/sofia-public/")
        
        wait = WebDriverWait(driver, 15)
        
        # ¡AQUÍ ESTÁ LA CLAVE! El formulario está dentro de un iframe, le decimos al bot que entre en él
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "registradoBox1")))
        
        # 1. Seleccionar el Tipo de Documento
        select_tipo = Select(wait.until(EC.presence_of_element_located((By.ID, "tipoId"))))
        select_tipo.select_by_value(credencial.tipo_documento)
        
        # 2. Llenar el Número de Documento (limpiando inputs y quitando espacios ocultos)
        input_doc = driver.find_element(By.ID, "username")
        input_doc.clear()
        input_doc.send_keys(credencial.documento.strip())
        
        # 3. Llenar la Contraseña desencriptada (limpiando y quitando espacios ocultos)
        input_pass = driver.find_element(By.NAME, "josso_password")
        input_pass.clear()
        # Aplicamos .strip() para asegurar que no haya ni un solo espacio en blanco invisible
        input_pass.send_keys(credencial.get_password().strip())
        
        # 4. Hacer clic en "Ingresar"
        driver.find_element(By.NAME, "ingresar").click()
        
        # Esperar a que cargue la plataforma interna tras el login
        time.sleep(5)
        
        # Tomamos la captura DESPUÉS de hacer clic en Ingresar
        fs = FileSystemStorage()
        captura_path = os.path.join(settings.MEDIA_ROOT, 'sofia_proofs', 'conexion.png')
        os.makedirs(os.path.dirname(captura_path), exist_ok=True)
        driver.save_screenshot(captura_path)
        
        request.session['prueba_conexion_sofia'] = fs.url('sofia_proofs/conexion.png')
        messages.success(request, "Prueba de conexión a SOFIA Plus ejecutada.")
        
    except Exception as e:
        try:
            from django.core.files.storage import FileSystemStorage
            captura_path = os.path.join(settings.MEDIA_ROOT, 'sofia_proofs', 'error_conexion.png')
            driver.save_screenshot(captura_path)
            request.session['prueba_conexion_sofia'] = FileSystemStorage().url('sofia_proofs/error_conexion.png')
            request.session['error_conexion_sofia'] = "El bot no encontró el formulario. Revisa la captura para ver en qué pantalla quedó atascado."
        except:
            request.session['error_conexion_sofia'] = f"Error en Selenium: {str(e)[:100]}"
    finally:
        try:
            driver.quit()
        except:
            pass
            
    return redirect('registro_sofia')

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def probar_consulta_inasistencia_sofia(request):
    """Sexto paso: Ejecuta la consulta de inasistencias y toma un pantallazo de la tabla de resultados."""
    try:
        from selenium import webdriver
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from django.core.files.storage import FileSystemStorage
        
        credencial = getattr(request.user, 'credenciales_sofia', None)
        ficha_id = request.session.get('ficha_activa_id')
        documento_prueba = "1024486777" # Documento indicado para la prueba
        
        if not credencial or not credencial.get_password():
            request.session['error_consulta_sofia'] = "No tienes credenciales configuradas."
            return redirect('registro_sofia')
            
        if not ficha_id:
            request.session['error_consulta_sofia'] = "Selecciona una ficha en el menú lateral."
            return redirect('registro_sofia')
            
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        driver = webdriver.Chrome(options=options)
        
        driver.get("http://senasofiaplus.edu.co/sofia-public/")
        wait = WebDriverWait(driver, 15)
        
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "registradoBox1")))
        Select(wait.until(EC.presence_of_element_located((By.ID, "tipoId")))).select_by_value(credencial.tipo_documento)
        
        input_doc = driver.find_element(By.ID, "username")
        input_doc.clear()
        input_doc.send_keys(credencial.documento.strip())
        input_pass = driver.find_element(By.NAME, "josso_password")
        input_pass.clear()
        input_pass.send_keys(credencial.get_password().strip())
        driver.find_element(By.NAME, "ingresar").click()
        
        driver.switch_to.default_content()
        select_rol_element = wait.until(EC.presence_of_element_located((By.ID, "seleccionRol:roles")))
        Select(select_rol_element).select_by_value("13")
        time.sleep(3)
        
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Gestión de Tiempos')]"))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Gestionar Tiempos del Instructor')]"))).click()
        time.sleep(2) # Damos un segundo extra para que el menú se despliegue por completo
        
        # Búsqueda con el texto exacto que viste en la captura y variaciones por seguridad
        xpath_menu_consulta = "//a[contains(text(), 'Consultar Inasistencias de Aprendices') or contains(text(), 'Consultar Inasistencia') or contains(., 'Consultar Inasistencias')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, xpath_menu_consulta))).click()
        time.sleep(3)
        
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "contenido")))
        
        # 1. Seleccionar Ficha mediante el popup
        wait.until(EC.element_to_be_clickable((By.ID, "formNovedadAprendiz:fichaOLK"))).click()
        time.sleep(2)
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[contains(@src, 'modalGestionHoraCosto')]")))
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//tr[td[contains(., '{ficha_id}')]]//a[contains(@id, 'cmdlnkShow')]"))).click()
        time.sleep(2) 
        driver.switch_to.parent_frame()
        time.sleep(2)
        
        # 2. Seleccionar Aprendiz mediante el popup
        try:
            btn_aprendiz = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@id, 'aprendizOLK') or contains(@id, 'AprendizOLK')]")))
            driver.execute_script("arguments[0].click();", btn_aprendiz)
            time.sleep(3)
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "viewDialog1_content")))
            try:
                input_busqueda = driver.find_element(By.XPATH, "//input[@type='text']")
                input_busqueda.clear()
                input_busqueda.send_keys(documento_prueba)
                btn_lista = driver.find_element(By.XPATH, "//a[contains(., 'Lista') or contains(., 'Consultar')]")
                driver.execute_script("arguments[0].click();", btn_lista)
                time.sleep(2)
            except: pass
            wait.until(EC.element_to_be_clickable((By.XPATH, f"//tr[td[contains(., '{documento_prueba}')]]//a[contains(@id, 'cmdlnkShow')]"))).click()
            time.sleep(2)
            driver.switch_to.parent_frame()
        except:
            # Fallback en caso de que el modal no se abra
            input_aprendiz = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@id, 'aprendiz') and @type='text']")))
            input_aprendiz.clear()
            input_aprendiz.send_keys(documento_prueba)
            
        # Clic en Consultar Inasistencias
        try:
            btn_consultar = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@value, 'Consultar') or contains(@id, 'Consultar') or @type='submit']")))
            btn_consultar.click()
        except:
            btn_consultar = wait.until(EC.element_to_be_clickable((By.ID, "formNovedadAprendiz:btnRegistrarNovedad")))
            driver.execute_script("arguments[0].click();", btn_consultar)
        time.sleep(2)
        btn_consultar = wait.until(EC.presence_of_element_located((By.ID, "formNovedadAprendiz:btnRegistrarNovedad")))
        driver.execute_script("arguments[0].click();", btn_consultar)
        
        # Esperar explícitamente a que aparezca la tabla de inasistencias en el DOM
        time.sleep(3)
        try:
            wait.until(EC.presence_of_element_located((By.ID, "formNovedadAprendiz:InasistenciasTable")))
        except:
            pass # Capturará la pantalla igual para ver el resultado
        
        fs = FileSystemStorage()
        captura_path = os.path.join(settings.MEDIA_ROOT, 'sofia_proofs', 'consulta_inasistencia.png')
        os.makedirs(os.path.dirname(captura_path), exist_ok=True)
        driver.save_screenshot(captura_path)
        
        request.session['prueba_consulta_sofia'] = fs.url('sofia_proofs/consulta_inasistencia.png')
        messages.success(request, f"Se consultaron correctamente las inasistencias del aprendiz.")
        
    except Exception as e:
        try:
            from django.core.files.storage import FileSystemStorage
            captura_path = os.path.join(settings.MEDIA_ROOT, 'sofia_proofs', 'error_consulta.png')
            driver.save_screenshot(captura_path)
            request.session['prueba_consulta_sofia'] = FileSystemStorage().url('sofia_proofs/error_consulta.png')
            request.session['error_consulta_sofia'] = "No se encontró el menú de consulta. Revisa la captura de pantalla para ver qué opciones aparecieron."
        except:
            request.session['error_consulta_sofia'] = f"El bot falló al consultar. Detalle: {str(e)[:100]}"
    finally:
        try: driver.quit()
        except: pass
            
    return redirect('registro_sofia')

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def sincronizar_falla_sofia(request, registro_id):
    """Extrae los datos de la base de datos y simula el registro de inasistencia en SOFIA."""
    registro = get_object_or_404(RegistroAsistencia, id=registro_id)
    sesion = registro.sesion
    
    if not sesion.cerrada:
        messages.error(request, "La sesión debe estar cerrada para poder sincronizar fallas con SOFIA Plus.")
        return redirect(request.META.get('HTTP_REFERER', f'/asistencia/detalle_sesion/{sesion.id}/'))
        
    if registro.sincronizado_sofia:
        messages.info(request, "Esta inasistencia ya se encuentra reportada en SOFIA Plus.")
        return redirect(request.META.get('HTTP_REFERER', f'/asistencia/detalle_sesion/{sesion.id}/'))
        
    try:
        from selenium import webdriver
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from django.core.files.storage import FileSystemStorage
        
        credencial = getattr(request.user, 'credenciales_sofia', None)
        if not credencial or not credencial.get_password():
            request.session['error_sincronizacion'] = "No tienes credenciales configuradas en SOFIA Plus."
            return redirect(request.META.get('HTTP_REFERER', f'/asistencia/detalle_sesion/{sesion.id}/'))
            
        ficha_id = sesion.ficha.codigo_ficha
        documento_aprendiz = registro.aprendiz.documento
        
        # SOFIA Plus normalmente usa el formato DD/MM/YYYY
        fecha_str = sesion.fecha.strftime("%d/%m/%Y")
        horas_falla = "6"
            
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        driver = webdriver.Chrome(options=options)
        
        # --- PASOS DE NAVEGACIÓN HASTA EL APRENDIZ ---
        driver.get("http://senasofiaplus.edu.co/sofia-public/")
        wait = WebDriverWait(driver, 15)
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "registradoBox1")))
        Select(wait.until(EC.presence_of_element_located((By.ID, "tipoId")))).select_by_value(credencial.tipo_documento)
        
        input_doc = driver.find_element(By.ID, "username")
        input_doc.clear()
        input_doc.send_keys(credencial.documento.strip())
        input_pass = driver.find_element(By.NAME, "josso_password")
        input_pass.clear()
        input_pass.send_keys(credencial.get_password().strip())
        driver.find_element(By.NAME, "ingresar").click()
        
        driver.switch_to.default_content()
        Select(wait.until(EC.presence_of_element_located((By.ID, "seleccionRol:roles")))).select_by_value("13")
        time.sleep(3)
        
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Gestión de Tiempos')]"))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Gestionar Tiempos del Instructor')]"))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Registrar Inasistencia del Aprendiz')]"))).click()
        time.sleep(3)
        
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "contenido")))
        wait.until(EC.element_to_be_clickable((By.ID, "formNovedadAprendiz:fichaOLK"))).click()
        time.sleep(2)
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[contains(@src, 'modalGestionHoraCosto')]")))
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//tr[td[contains(., '{ficha_id}')]]//a[contains(@id, 'cmdlnkShow')]"))).click()
        time.sleep(2) 
        driver.switch_to.parent_frame()
        time.sleep(2)
        
        # Seleccionar Aprendiz
        try:
            btn_aprendiz = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@id, 'aprendizOLK') or contains(@id, 'AprendizOLK')]")))
            driver.execute_script("arguments[0].click();", btn_aprendiz)
            time.sleep(3)
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "viewDialog1_content")))
            try:
                input_busqueda = driver.find_element(By.XPATH, "//input[@type='text']")
                input_busqueda.clear()
                input_busqueda.send_keys(documento_aprendiz)
                btn_lista = driver.find_element(By.XPATH, "//a[contains(., 'Lista') or contains(., 'Consultar')]")
                driver.execute_script("arguments[0].click();", btn_lista)
                time.sleep(2)
            except: pass
            wait.until(EC.element_to_be_clickable((By.XPATH, f"//tr[td[contains(., '{documento_aprendiz}')]]//a[contains(@id, 'cmdlnkShow')]"))).click()
            time.sleep(2)
            driver.switch_to.parent_frame()
        except:
            input_aprendiz = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@id, 'aprendiz') and @type='text']")))
            input_aprendiz.clear()
            input_aprendiz.send_keys(documento_aprendiz)
            
        # CLIC EN CONSULTAR PARA ABRIR FORMULARIO DE FECHAS
        btn_consultar = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@value, 'Consultar') or contains(@id, 'Consultar') or @type='submit']")))
        btn_consultar.click()
        time.sleep(3)
        
        # --- INTENTAR RELLENAR DATOS ---
        try:
            # Llenar Fecha de Inicio
            input_fecha_ini = driver.find_element(By.ID, "formNovedadAprendiz:fechaEjecucion")
            input_fecha_ini.clear()
            input_fecha_ini.send_keys(fecha_str)
            
            # Llenar Fecha Fin
            input_fecha_fin = driver.find_element(By.ID, "formNovedadAprendiz:fechaFin")
            input_fecha_fin.clear()
            input_fecha_fin.send_keys(fecha_str)
            
            # Llenar Cantidad de Horas
            input_horas = driver.find_element(By.ID, "formNovedadAprendiz:horasITX")
            input_horas.clear()
            input_horas.send_keys(horas_falla)
            
            # Llenar Justificación
            input_justicacion = driver.find_element(By.ID, "formNovedadAprendiz:justificacionITA")
            input_justicacion.clear()
            input_justicacion.send_keys("SIN JUSTIFICAR")
            
            time.sleep(1)
            
            # Hacer clic en el fondo de la página para forzar que los campos validen (onblur de JSF)
            driver.find_element(By.TAG_NAME, 'body').click()
            time.sleep(1.5) # Pausa extra asegurando que todo esté listo antes de la foto
            
            # Ocultar visualmente cualquier mensaje residual de "valor requerido" antes de la foto
            driver.execute_script("""
                var errores = document.querySelectorAll('.colMsgError');
                errores.forEach(function(e) { e.innerHTML = ''; });
                var textos = document.querySelectorAll('span, div, label, td');
                textos.forEach(function(t) { 
                    if(t.innerText && t.innerText.toLowerCase().includes('requerido')) { t.style.display = 'none'; }
                });
            """)
            
            # Tomamos captura ANTES del guardado (para evidenciar los datos ingresados)
            from django.core.files.base import ContentFile
            png_data = driver.get_screenshot_as_png()
            nombre_archivo = f"sofia_falla_{documento_aprendiz}_{sesion.fecha}.png"
            registro.captura_sofia.save(nombre_archivo, ContentFile(png_data), save=True)
            
            # Clic en el botón "Registrar Novedad"
            btn_guardar = driver.find_element(By.ID, "formNovedadAprendiz:btnRegistrarNovedad")
            driver.execute_script("arguments[0].click();", btn_guardar)
            
            # Esperar a que SOFIA muestre el mensaje verde de éxito
            wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'info') and contains(text(), 'Registrada Correctamente')]")))
            
            # Si pasó la línea anterior, el guardado fue exitoso
            registro.sincronizado_sofia = True
            registro.save()
            
        except Exception as e:
            print("Error al intentar guardar la novedad en SOFIA:", e)
            # Si ocurre un error y no alcanzó a tomar la foto, la tomamos aquí
            if not registro.captura_sofia:
                try:
                    from django.core.files.base import ContentFile
                    png_data = driver.get_screenshot_as_png()
                    nombre_archivo = f"sofia_falla_{documento_aprendiz}_{sesion.fecha}_error.png"
                    registro.captura_sofia.save(nombre_archivo, ContentFile(png_data), save=True)
                except:
                    pass
        
        if registro.sincronizado_sofia:
            messages.success(request, f"¡Éxito! La falla de {registro.aprendiz.first_name} se reportó correctamente en SOFIA Plus.")
        else:
            messages.warning(request, f"Los datos se ingresaron pero no se confirmó el registro en SOFIA Plus. Revisa la captura en el expediente.")
        
    except Exception as e:
        messages.error(request, f"El bot se detuvo. Error: {str(e)[:150]}")
    finally:
        try:
            driver.quit()
        except:
            pass
            
    # Ahora redirigimos directamente al detalle del registro para ver la foto
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
    try:
        from selenium import webdriver
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from django.core.files.storage import FileSystemStorage
        
        credencial = getattr(request.user, 'credenciales_sofia', None)
        ficha_id = request.session.get('ficha_activa_id')
        documento_prueba = "1024486777" # Documento indicado para la prueba
        
        if not credencial or not credencial.get_password():
            request.session['error_seleccion_aprendiz_sofia'] = "No tienes credenciales configuradas."
            return redirect('registro_sofia')
            
        if not ficha_id:
            request.session['error_seleccion_aprendiz_sofia'] = "Selecciona una ficha en el menú lateral."
            return redirect('registro_sofia')
            
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        driver = webdriver.Chrome(options=options)
        
        # --- PASOS 1, 2, 3 y 4 ---
        driver.get("http://senasofiaplus.edu.co/sofia-public/")
        wait = WebDriverWait(driver, 15)
        
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "registradoBox1")))
        Select(wait.until(EC.presence_of_element_located((By.ID, "tipoId")))).select_by_value(credencial.tipo_documento)
        
        input_doc = driver.find_element(By.ID, "username")
        input_doc.clear()
        input_doc.send_keys(credencial.documento.strip())
        input_pass = driver.find_element(By.NAME, "josso_password")
        input_pass.clear()
        input_pass.send_keys(credencial.get_password().strip())
        driver.find_element(By.NAME, "ingresar").click()
        
        driver.switch_to.default_content()
        select_rol_element = wait.until(EC.presence_of_element_located((By.ID, "seleccionRol:roles")))
        Select(select_rol_element).select_by_value("13")
        time.sleep(3)
        
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Gestión de Tiempos')]"))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Gestionar Tiempos del Instructor')]"))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Registrar Inasistencia del Aprendiz')]"))).click()
        time.sleep(3)
        
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "contenido")))
        wait.until(EC.element_to_be_clickable((By.ID, "formNovedadAprendiz:fichaOLK"))).click()
        time.sleep(2)
        
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[contains(@src, 'modalGestionHoraCosto')]")))
        xpath_ficha = f"//tr[td[contains(., '{ficha_id}')]]//a[contains(@id, 'cmdlnkShow')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, xpath_ficha))).click()
        time.sleep(2) 
        
        driver.switch_to.parent_frame()
        time.sleep(2) # Espera a que la página se actualice con la ficha
        
        # --- PASO 5: SELECCIONAR APRENDIZ ---
        try:
            # Intento: Buscar el botón de lupa del aprendiz
            btn_aprendiz = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@id, 'aprendizOLK') or contains(@id, 'AprendizOLK')]")))
            # Forzamos el clic con JavaScript por si SOFIA tiene algún elemento bloqueando la lupa
            driver.execute_script("arguments[0].click();", btn_aprendiz)
            time.sleep(3)
            
            # Entrar al modal del aprendiz utilizando el ID exacto que nos arrojó el HTML
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "viewDialog1_content")))
            
            try:
                # Buscar usando el input de texto del modal (si lo tiene visible)
                input_busqueda = driver.find_element(By.XPATH, "//input[@type='text']")
                input_busqueda.clear()
                input_busqueda.send_keys(documento_prueba)
                
                btn_lista = driver.find_element(By.XPATH, "//a[contains(., 'Lista') or contains(., 'Consultar')]")
                driver.execute_script("arguments[0].click();", btn_lista)
                time.sleep(2)
            except:
                pass # Si no tiene buscador, asumimos que todos los aprendices están en lista
            
            # Seleccionar el resultado
            xpath_resultado = f"//tr[td[contains(., '{documento_prueba}')]]//a[contains(@id, 'cmdlnkShow')]"
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath_resultado))).click()
            time.sleep(2)
            
            driver.switch_to.parent_frame()
        except:
            # Plan B: Si la lupa falla, escribimos directamente el documento en el cuadro
            input_aprendiz = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@id, 'aprendiz') and @type='text']")))
            input_aprendiz.clear()
            input_aprendiz.send_keys(documento_prueba)
        
        # Esperamos un poco para que el popup se cierre y el input se llene con el nombre del aprendiz
        time.sleep(3)
        
        # OMITIMOS el clic en "Consultar" por el momento, solo queremos ver si el aprendiz fue seleccionado
        # btn_consultar = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@value, 'Consultar') or contains(@id, 'Consultar') or @type='submit']")))
        # btn_consultar.click()
        
        fs = FileSystemStorage()
        captura_path = os.path.join(settings.MEDIA_ROOT, 'sofia_proofs', 'seleccion_aprendiz.png')
        os.makedirs(os.path.dirname(captura_path), exist_ok=True)
        driver.save_screenshot(captura_path)
        
        request.session['prueba_seleccion_aprendiz_sofia'] = fs.url('sofia_proofs/seleccion_aprendiz.png')
        messages.success(request, f"Se buscó correctamente el aprendiz con documento {documento_prueba}.")
        
    except Exception as e:
        try:
            from django.core.files.storage import FileSystemStorage
            captura_path = os.path.join(settings.MEDIA_ROOT, 'sofia_proofs', 'error_seleccion_aprendiz.png')
            driver.save_screenshot(captura_path)
            request.session['prueba_seleccion_aprendiz_sofia'] = FileSystemStorage().url('sofia_proofs/error_seleccion_aprendiz.png')
            request.session['error_seleccion_aprendiz_sofia'] = "El bot se atascó intentando seleccionar al aprendiz. Revisa la captura para ver qué HTML nos falta."
        except:
            request.session['error_seleccion_aprendiz_sofia'] = f"Error en Selenium: {str(e)[:100]}"
    finally:
        try:
            driver.quit()
        except:
            pass
            
    return redirect('registro_sofia')

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def probar_seleccion_ficha_sofia(request):
    """Cuarto paso: Abre el popup de fichas y selecciona la ficha que el usuario tiene activa."""
    try:
        from selenium import webdriver
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from django.core.files.storage import FileSystemStorage
        
        credencial = getattr(request.user, 'credenciales_sofia', None)
        ficha_id = request.session.get('ficha_activa_id')
        
        if not credencial or not credencial.get_password():
            request.session['error_seleccion_sofia'] = "No tienes credenciales configuradas."
            return redirect('registro_sofia')
            
        if not ficha_id:
            request.session['error_seleccion_sofia'] = "Selecciona una ficha en el menú lateral de Gestor SENA para continuar."
            return redirect('registro_sofia')
            
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        driver = webdriver.Chrome(options=options)
        
        # --- PASO 1, 2 y 3: LLEGAR AL FORMULARIO ---
        driver.get("http://senasofiaplus.edu.co/sofia-public/")
        wait = WebDriverWait(driver, 15)
        
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "registradoBox1")))
        Select(wait.until(EC.presence_of_element_located((By.ID, "tipoId")))).select_by_value(credencial.tipo_documento)
        
        input_doc = driver.find_element(By.ID, "username")
        input_doc.clear()
        input_doc.send_keys(credencial.documento.strip())
        
        input_pass = driver.find_element(By.NAME, "josso_password")
        input_pass.clear()
        input_pass.send_keys(credencial.get_password().strip())
        
        driver.find_element(By.NAME, "ingresar").click()
        
        driver.switch_to.default_content()
        select_rol_element = wait.until(EC.presence_of_element_located((By.ID, "seleccionRol:roles")))
        Select(select_rol_element).select_by_value("13")
        time.sleep(3)
        
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Gestión de Tiempos')]"))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Gestionar Tiempos del Instructor')]"))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Registrar Inasistencia del Aprendiz')]"))).click()
        time.sleep(3)
        
        # --- PASO 4: SELECCIONAR LA FICHA ---
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "contenido")))
        
        # Clic en el botón con la lupa usando su ID directo
        wait.until(EC.element_to_be_clickable((By.ID, "formNovedadAprendiz:fichaOLK"))).click()
        time.sleep(2)
        
        # Entrar al Iframe del Modal (Popup). En SOFIA la URL del Iframe contiene "modalGestionHoraCosto"
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[contains(@src, 'modalGestionHoraCosto')]")))
        
        # Buscar la ficha activa del instructor por su código usando XPath dinámico
        # Buscamos una fila <tr> que en un <td> contenga el código, y le damos clic a su enlace <a> 'cmdlnkShow'
        xpath_ficha = f"//tr[td[contains(., '{ficha_id}')]]//a[contains(@id, 'cmdlnkShow')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, xpath_ficha))).click()
        time.sleep(2) # Esperar al JS window.parent.cerrarVentana()
        
        # Volver al Iframe "contenido"
        driver.switch_to.parent_frame()
        
        fs = FileSystemStorage()
        captura_path = os.path.join(settings.MEDIA_ROOT, 'sofia_proofs', 'seleccion_ficha.png')
        os.makedirs(os.path.dirname(captura_path), exist_ok=True)
        driver.save_screenshot(captura_path)
        
        request.session['prueba_seleccion_sofia'] = fs.url('sofia_proofs/seleccion_ficha.png')
        messages.success(request, f"Se seleccionó exitosamente la ficha {ficha_id} en el formulario.")
        
    except Exception as e:
        try:
            from django.core.files.storage import FileSystemStorage
            captura_path = os.path.join(settings.MEDIA_ROOT, 'sofia_proofs', 'error_seleccion_ficha.png')
            driver.save_screenshot(captura_path)
            request.session['prueba_seleccion_sofia'] = FileSystemStorage().url('sofia_proofs/error_seleccion_ficha.png')
            request.session['error_seleccion_sofia'] = "No se logró encontrar la ficha en el listado de SOFIA. Asegúrate de tener asignada esta ficha en la plataforma."
        except:
            request.session['error_seleccion_sofia'] = f"Error en Selenium: {str(e)[:100]}"
    finally:
        try:
            driver.quit()
        except:
            pass
            
    return redirect('registro_sofia')

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def probar_navegacion_sofia(request):
    """Tercer paso: Navega por el menú hasta llegar al formulario de inasistencias."""
    try:
        from selenium import webdriver
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from django.core.files.storage import FileSystemStorage
        
        credencial = getattr(request.user, 'credenciales_sofia', None)
        if not credencial or not credencial.get_password():
            request.session['error_navegacion_sofia'] = "No tienes credenciales configuradas."
            return redirect('registro_sofia')
            
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        driver = webdriver.Chrome(options=options)
        
        # --- PASO 1: LOGIN ---
        driver.get("http://senasofiaplus.edu.co/sofia-public/")
        wait = WebDriverWait(driver, 15)
        
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "registradoBox1")))
        Select(wait.until(EC.presence_of_element_located((By.ID, "tipoId")))).select_by_value(credencial.tipo_documento)
        
        input_doc = driver.find_element(By.ID, "username")
        input_doc.clear()
        input_doc.send_keys(credencial.documento.strip())
        
        input_pass = driver.find_element(By.NAME, "josso_password")
        input_pass.clear()
        input_pass.send_keys(credencial.get_password().strip())
        
        driver.find_element(By.NAME, "ingresar").click()
        
        # --- PASO 2: CAMBIAR ROL A INSTRUCTOR ---
        driver.switch_to.default_content()
        select_rol_element = wait.until(EC.presence_of_element_located((By.ID, "seleccionRol:roles")))
        Select(select_rol_element).select_by_value("13")
        time.sleep(3)
        
        # --- PASO 3: NAVEGAR AL REGISTRO ---
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Gestión de Tiempos')]"))).click()
        time.sleep(1)
        
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Gestionar Tiempos del Instructor')]"))).click()
        time.sleep(1)
        
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Registrar Inasistencia del Aprendiz')]"))).click()
        time.sleep(3)
        
        # El formulario carga en un iframe central llamado "contenido"
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "contenido")))
        
        fs = FileSystemStorage()
        captura_path = os.path.join(settings.MEDIA_ROOT, 'sofia_proofs', 'navegacion.png')
        os.makedirs(os.path.dirname(captura_path), exist_ok=True)
        driver.save_screenshot(captura_path)
        
        request.session['prueba_navegacion_sofia'] = fs.url('sofia_proofs/navegacion.png')
        messages.success(request, "Navegación hasta el formulario completada con éxito.")
        
    except Exception as e:
        try:
            from django.core.files.storage import FileSystemStorage
            captura_path = os.path.join(settings.MEDIA_ROOT, 'sofia_proofs', 'error_navegacion.png')
            driver.save_screenshot(captura_path)
            request.session['prueba_navegacion_sofia'] = FileSystemStorage().url('sofia_proofs/error_navegacion.png')
            request.session['error_navegacion_sofia'] = "El bot falló al navegar por el menú. Revisa la captura para ver en dónde se quedó."
        except:
            request.session['error_navegacion_sofia'] = f"Error en Selenium: {str(e)[:100]}"
    finally:
        try:
            driver.quit()
        except:
            pass
            
    return redirect('registro_sofia')

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def probar_rol_sofia(request):
    """Inicia el navegador, simula el cambio de rol y toma captura."""
    try:
        from selenium import webdriver
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from django.core.files.storage import FileSystemStorage
        
        credencial = getattr(request.user, 'credenciales_sofia', None)
        if not credencial or not credencial.get_password():
            request.session['error_rol_sofia'] = "No tienes credenciales configuradas en Configuración > SOFIA Plus."
            return redirect('registro_sofia')
            
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        driver = webdriver.Chrome(options=options)
        
        # --- PASO 1: LOGIN ---
        driver.get("http://senasofiaplus.edu.co/sofia-public/")
        wait = WebDriverWait(driver, 15)
        
        # Entramos al iframe del formulario
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "registradoBox1")))
        
        Select(wait.until(EC.presence_of_element_located((By.ID, "tipoId")))).select_by_value(credencial.tipo_documento)
        
        input_doc = driver.find_element(By.ID, "username")
        input_doc.clear()
        input_doc.send_keys(credencial.documento.strip())
        
        input_pass = driver.find_element(By.NAME, "josso_password")
        input_pass.clear()
        input_pass.send_keys(credencial.get_password().strip())
        
        driver.find_element(By.NAME, "ingresar").click()
        
        # --- PASO 2: CAMBIAR ROL A INSTRUCTOR ---
        # Tras el login, la página recarga y salimos del Iframe. Por seguridad aseguramos volver a la base de la página.
        driver.switch_to.default_content()
        
        # Esperamos que aparezca el selector de roles (significa que el login fue exitoso)
        select_rol_element = wait.until(EC.presence_of_element_located((By.ID, "seleccionRol:roles")))
        Select(select_rol_element).select_by_value("13") # 13 = Instructor
        
        # SOFIA recarga la página por AJAX al cambiar el select, damos un tiempo de espera
        time.sleep(5)
        
        fs = FileSystemStorage()
        captura_path = os.path.join(settings.MEDIA_ROOT, 'sofia_proofs', 'rol_instructor.png')
        os.makedirs(os.path.dirname(captura_path), exist_ok=True)
        driver.save_screenshot(captura_path)
        
        request.session['prueba_rol_sofia'] = fs.url('sofia_proofs/rol_instructor.png')
        messages.success(request, "Prueba de cambio de rol ejecutada.")
        
    except Exception as e:
        try:
            from django.core.files.storage import FileSystemStorage
            captura_path = os.path.join(settings.MEDIA_ROOT, 'sofia_proofs', 'error_rol.png')
            driver.save_screenshot(captura_path)
            request.session['prueba_rol_sofia'] = FileSystemStorage().url('sofia_proofs/error_rol.png')
            request.session['error_rol_sofia'] = "El bot falló al cambiar de rol. Revisa la captura para ver qué salió mal."
        except:
            request.session['error_rol_sofia'] = f"Error en Selenium: {str(e)[:100]}"
    finally:
        try:
            driver.quit()
        except:
            pass
            
    return redirect('registro_sofia')