from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from usuarios.decorators import rol_requerido
from .models import Usuario, Ficha
from .forms import UsuarioForm, UsuarioEditarForm, FichaForm, FichaEditarForm
from datetime import datetime

from asistencia.models import RegistroAsistencia
from fondos.models import Movimiento
from llamados.models import LlamadoAtencion
from planeacion.models import ActividadPlaneacion

@login_required
def inicio_usuario(request):
    lista_usuarios = Usuario.objects.all().order_by('last_name')

    context = {
        'nombre': 'Antony',
        'titulo': 'Usuarios y Roles',
        'breadcrumbs': [
            
            {'nombre': 'Usuarios', 'url': ''} 
        ],
        'usuarios_ficha': lista_usuarios,
    }
    return render(request, 'usuarios/inicio_usuarios.html', context)
@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST, request.FILES) 
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.username = usuario.documento
            
            inicial_nombre = usuario.first_name[0].upper()
            inicial_apellido = usuario.last_name[0].upper()
            password_generada = f"#{inicial_nombre}{inicial_apellido}{usuario.documento}"
            
            usuario.set_password(password_generada)
            usuario.save()
            
            # Cambiamos "Aprendiz" por "Usuario"
            mensaje = f"¡Usuario {usuario.first_name} registrado! Ingreso: {usuario.documento} | Clave: {password_generada}"
            messages.success(request, mensaje)
            
            return redirect('usuarios/inicio_usuario')
        else:
            messages.error(request, "Error al registrar. Por favor verifica los datos.")
    else:
        form = UsuarioForm()

    context = {
        'form': form,
        'titulo': 'Registrar Nuevo Usuario', # Renombrado
        'breadcrumbs': [
            
            {'nombre': 'Usuarios', 'url': '/usuarios/'},
            {'nombre': 'Nuevo Usuario', 'url': ''}
        ],
    }
    return render(request, 'usuarios/agregar_usuarios.html', context)
@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        form = UsuarioEditarForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f"Datos de {usuario.first_name} actualizados correctamente.")
            return redirect('inicio_usuario')
        else:
            messages.error(request, "Error al actualizar. Revisa los campos marcados en rojo.")
    else:
        form = UsuarioEditarForm(instance=usuario)

    context = {
        'form': form,
        'titulo': f'Editar a {usuario.first_name}',
        'breadcrumbs': [
            {'nombre': 'Usuarios', 'url': '/usuarios/usuario'},
            {'nombre': 'Editar Usuario', 'url': ''}
        ],
    }
    return render(request, 'usuarios/agregar_usuarios.html', context)


@login_required
def set_ficha_activa(request):
    """
    Recibe el ID de la ficha desde el selector del menú lateral,
    lo guarda en la sesión del usuario y recarga la página.
    """
    # Verificamos que la petición venga del formulario (POST)
    if request.method == 'POST':
        # Atrapamos el ID ('ficha_id' es el atributo name="..." del <select>)
        ficha_id = request.POST.get('ficha_id')
        
        if ficha_id:
            # ¡Aquí ocurre la magia! Se guarda en la "mochila" del usuario (la sesión)
            request.session['ficha_activa_id'] = ficha_id
            # Opcional: Enviamos un mensaje de confirmación
            messages.success(request, "Contexto actualizado correctamente.")
            
        # Lo devolvemos exactamente a la misma página en la que estaba
        # (HTTP_REFERER guarda la URL anterior. Si falla, lo manda a '/')
        return redirect(request.META.get('HTTP_REFERER', '/'))
        
    # Si alguien intenta acceder a esta URL escribiéndola en el navegador (GET), lo echamos al inicio
    return redirect('/')

@login_required
def inicio_ficha(request):
    # 1. Leemos el código de la ficha que el instructor seleccionó en el menú lateral
    codigo_seleccionado = request.session.get('ficha_activa_id')

    # Si NO hay ficha seleccionada, renderizamos el HTML (el {% if ficha_activa %} mostrará la alerta)
    if not codigo_seleccionado:
        return render(request, 'fichas/inicio_ficha.html', {'titulo': 'Panel de Ficha'})

    # 2. Obtenemos la ficha usando tu campo codigo_ficha
    ficha = get_object_or_404(Ficha, codigo_ficha=codigo_seleccionado)
    
    # 3. Lógica de Aprendices (Métricas para las tarjetas)
    aprendices = Usuario.objects.filter(ficha=ficha, rol='APRENDIZ')
    total_aprendices = aprendices.count()
    aprendices_activos = aprendices.filter(is_active=True).count()
    aprendices_retirados = total_aprendices - aprendices_activos
    
    # 4. Lógica del Equipo Ejecutor (Tabla de Instructores)
    equipo_ejecutor = Usuario.objects.filter(ficha=ficha, rol='INSTRUCTOR')
    
    # 4.1 Instructores disponibles para asignar (que NO están en esta ficha)
    instructores_asignados_ids = equipo_ejecutor.values_list('id', flat=True)
    instructores_disponibles = Usuario.objects.filter(
        rol='INSTRUCTOR', 
        is_active=True
    ).exclude(id__in=instructores_asignados_ids).order_by('first_name', 'last_name')
    
    # 5. Lógica de Cumpleaños por Trimestre
    mes_actual = datetime.now().month
    if mes_actual <= 3:
        trimestre_actual = [1, 2, 3]
        trimestre_proximo = [4, 5, 6]
    elif mes_actual <= 6:
        trimestre_actual = [4, 5, 6]
        trimestre_proximo = [7, 8, 9]
    elif mes_actual <= 9:
        trimestre_actual = [7, 8, 9]
        trimestre_proximo = [10, 11, 12]
    else:
        trimestre_actual = [10, 11, 12]
        trimestre_proximo = [1, 2, 3]
    
    cumpleaños_trimestre_actual = Usuario.objects.filter(ficha=ficha, fecha_nacimiento__month__in=trimestre_actual).order_by('fecha_nacimiento__month', 'fecha_nacimiento__day')
    cumpleaños_trimestre_proximo = Usuario.objects.filter(ficha=ficha, fecha_nacimiento__month__in=trimestre_proximo).order_by('fecha_nacimiento__month', 'fecha_nacimiento__day')
    
    # 6. Cálculo de progreso del Proyecto Formativo (Fases)
    actividades = ActividadPlaneacion.objects.filter(ficha=ficha)
    
    def calcular_progreso(fase_nombre):
        acts_fase = actividades.filter(fase=fase_nombre)
        total = acts_fase.count()
        if total == 0:
            return 0  # Si no hay actividades programadas, el progreso es 0%
        terminadas = acts_fase.filter(estado='Terminada').count()
        return int((terminadas / total) * 100)

    progreso_analisis = calcular_progreso('Analisis')
    progreso_planeacion = calcular_progreso('Planeacion')
    progreso_ejecucion = calcular_progreso('Ejecucion')
    progreso_evaluacion = calcular_progreso('Evaluacion')

    # 7. Construcción dinámica de tus Breadcrumbs (Migas de pan)
    breadcrumbs = [
         
        {'nombre': f'Ficha {ficha.codigo_ficha}', 'url': ''}
    ]
    
    # 6. Empaquetamos todo en el contexto
    context = {
        'titulo': f'Panel de Ficha {ficha.codigo_ficha}',
        # Nota: Ya no pasamos 'ficha': ficha, porque tu Context Processor ya inyecta 'ficha_activa'
        'total_aprendices': total_aprendices,
        'aprendices_activos': aprendices_activos,
        'aprendices_retirados': aprendices_retirados,
        'equipo_ejecutor': equipo_ejecutor,
        'instructores_disponibles': instructores_disponibles,
        'cumpleaños_trimestre_actual': cumpleaños_trimestre_actual,
        'cumpleaños_trimestre_proximo': cumpleaños_trimestre_proximo,
        'progreso_analisis': progreso_analisis,
        'progreso_planeacion': progreso_planeacion,
        'progreso_ejecucion': progreso_ejecucion,
        'progreso_evaluacion': progreso_evaluacion,
        'breadcrumbs': breadcrumbs,
    }
    
    return render(request, 'fichas/inicio_ficha.html', context)

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def asignar_instructor_ficha(request):
    """Asigna un instructor a la ficha activa."""
    if request.method == 'POST':
        ficha_id = request.session.get('ficha_activa_id')
        instructor_id = request.POST.get('instructor_id')
        
        if not ficha_id:
            messages.error(request, "No hay una ficha activa seleccionada.")
            return redirect('inicio_ficha')
        
        if not instructor_id:
            messages.error(request, "Debes seleccionar un instructor.")
            return redirect('inicio_ficha')
        
        ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)
        instructor = get_object_or_404(Usuario, id=instructor_id, rol='INSTRUCTOR')
        
        # Asignar la ficha al instructor
        instructor.ficha = ficha
        instructor.save()
        
        messages.success(request, f"El instructor {instructor.get_full_name()} ha sido asignado a la ficha {ficha.codigo_ficha}.")
    
    return redirect('inicio_ficha')
@login_required
def listar_fichas(request):
    """Listado general de todas las fichas registradas en el sistema."""
    lista_fichas = Ficha.objects.all()

    context = {
        'titulo': 'Listado de Fichas',
        'breadcrumbs': [
            
            {'nombre': 'Fichas', 'url': ''}
        ],
        'fichas': lista_fichas,
    }
    
    return render(request, 'fichas/listar_fichas.html', context)
@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def crear_ficha(request):
    if request.method == 'POST':
        form = FichaForm(request.POST)
        if form.is_valid():
            ficha = form.save()
            ficha.save()
            
            mensaje = f"¡Ficha {ficha.codigo_ficha} registrada!"
            messages.success(request, mensaje)
            
            return redirect('inicio_ficha')
        else:
            messages.error(request, "Error al registrar. Por favor verifica los datos.")
    else:
        form = FichaForm()

    context = {
        'form': form,
        'titulo': 'Registrar Nueva Ficha',
        'breadcrumbs': [
            {'nombre': 'Ficha', 'url': '#'},
            {'nombre': 'Directorio', 'url': '/fichas/'}, 
            {'nombre': 'Nueva Ficha', 'url': ''}
        ],
    }
    return render(request, 'fichas/agregar_ficha.html', context)

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def editar_ficha(request, codigo_ficha):
    """Permite editar los detalles de una ficha y cambiar su estado activo/inactivo."""
    # Buscamos la ficha por su código, si no existe lanza un 404
    ficha = get_object_or_404(Ficha, codigo_ficha=codigo_ficha)

    if request.method == 'POST':
        # Pasamos la instancia de la ficha para que Django sepa que estamos actualizando, no creando
        form = FichaEditarForm(request.POST, instance=ficha)
        if form.is_valid():
            form.save()
            messages.success(request, f"Datos de la Ficha {ficha.codigo_ficha} actualizados correctamente.")
            return redirect('listar_fichas')
        else:
            messages.error(request, "Error al actualizar la ficha. Revisa los datos ingresados.")
    else:
        # Si es GET, cargamos el formulario con los datos actuales de la ficha
        form = FichaEditarForm(instance=ficha)

    context = {
        'form': form,
        'titulo': f'Editar Ficha {ficha.codigo_ficha}',
        'breadcrumbs': [
            {'nombre': 'Administración', 'url': '#'},
            {'nombre': 'Listado de Fichas', 'url': '/fichas/listar/'}, 
            {'nombre': 'Editar', 'url': ''}
        ],
    }
    
    # Reutilizamos el mismo template de agregar, ya que Crispy Forms se encarga de pintar los inputs
    return render(request, 'fichas/agregar_ficha.html', context)

@login_required
def informe_aprendiz(request, usuario_id):
    """Vista detallada con el reporte integral de un aprendiz: Asistencia, Llamados y Fondos."""
    aprendiz = get_object_or_404(Usuario, id=usuario_id)
    
    # 1. Asistencias (Solo Fallas y Excusas)
    asistencias = RegistroAsistencia.objects.filter(
        aprendiz=aprendiz, 
        estado__in=['Falla', 'Excusa']
    ).select_related('sesion').order_by('-sesion__fecha')
    
    # 2. Fondos (Multas, aportes u otros movimientos del usuario)
    movimientos = Movimiento.objects.filter(
        responsable=aprendiz
    ).select_related('concepto').order_by('-fecha')
    
    # 3. Llamados de atención disciplinarios o académicos
    llamados = LlamadoAtencion.objects.filter(
        aprendiz=aprendiz
    ).select_related('falta_cometida').order_by('-id')
    
    # Mensaje de advertencia sobre el Acuerdo 009 de 2012
    mensaje_acuerdo_009 = (
        "Según el Acuerdo 009 de 2012 (Reglamento del Aprendiz SENA): "
        "Las inasistencias justificadas (Excusas) no eximen al aprendiz de la responsabilidad de desatrasarse y presentar las evidencias de aprendizaje. "
        "A su vez, si el total de inasistencias (justificadas o no) supera el 10% de las horas totales de la etapa lectiva, "
        "se considera un incumplimiento que puede dar lugar al inicio del proceso de cancelación de matrícula por deserción."
    )
    
    context = {
        'titulo': f'Informe de {aprendiz.first_name} {aprendiz.last_name}',
        'aprendiz': aprendiz,
        'asistencias': asistencias,
        'movimientos': movimientos,
        'llamados': llamados,
        'mensaje_acuerdo_009': mensaje_acuerdo_009,
        'breadcrumbs': [
            {'nombre': 'Usuarios', 'url': '/usuarios/usuario/'},
            {'nombre': 'Informe Integral', 'url': ''}
        ],
    }
    return render(request, 'usuarios/informe_aprendiz.html', context)