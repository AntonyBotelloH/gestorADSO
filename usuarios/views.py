from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Usuario, Ficha
from .forms import UsuarioForm, UsuarioEditarForm, FichaForm

def inicio_usuario(request):
    lista_usuarios = Usuario.objects.all().order_by('first_name')

    context = {
        'nombre': 'Antony',
        'titulo': 'Usuarios y Roles',
        'breadcrumbs': [
            {'nombre': 'Ficha', 'url': '#'},
            {'nombre': 'Directorio', 'url': ''} 
        ],
        'usuarios_ficha': lista_usuarios,
    }
    return render(request, 'usuarios/inicio_usuarios.html', context)
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
            {'nombre': 'Ficha', 'url': '#'},
            {'nombre': 'Directorio', 'url': '/usuarios/'}, 
            {'nombre': 'Nuevo Usuario', 'url': ''} # Renombrado
        ],
    }
    return render(request, 'usuarios/agregar_usuarios.html', context)
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        form = UsuarioEditarForm(request.POST, instance=usuario)
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
            {'nombre': 'Ficha', 'url': '#'},
            {'nombre': 'Directorio', 'url': '/usuarios/'},
            {'nombre': 'Editar Aprendiz', 'url': ''}
        ],
    }
    return render(request, 'usuarios/agregar_usuarios.html', context)


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
    
    # 5. Construcción dinámica de tus Breadcrumbs (Migas de pan)
    breadcrumbs = [
        {'nombre': 'Inicio', 'url': '/'}, 
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
        'breadcrumbs': breadcrumbs,
    }
    
    return render(request, 'fichas/inicio_ficha.html', context)
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