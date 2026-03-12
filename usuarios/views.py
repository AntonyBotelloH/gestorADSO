from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Usuario
from .forms import UsuarioForm, UsuarioEditarForm

def inicio_usuario(request):
    lista_usuarios = Usuario.objects.all().order_by('first_name')

    context = {
        'nombre': 'Antony',
        'titulo': 'Aprendices y Roles',
        'breadcrumbs': [
            {'nombre': 'Ficha', 'url': '#'},
            {'nombre': 'Directorio', 'url': ''} 
        ],
        'usuarios_ficha': lista_usuarios,
    }
    return render(request, 'inicio_usuarios.html', context)


def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            
            # 1. Asignar el documento como nombre de usuario
            usuario.username = usuario.documento
            
            # 2. Construir la contraseña automática (# + Inicial N + Inicial A + Documento)
            # Usamos [0].upper() para sacar la primera letra y asegurarnos de que sea mayúscula
            inicial_nombre = usuario.first_name[0].upper()
            inicial_apellido = usuario.last_name[0].upper()
            
            password_generada = f"#{inicial_nombre}{inicial_apellido}{usuario.documento}"
            
            # 3. Encriptamos la contraseña generada
            usuario.set_password(password_generada)
            
            # 4. Ahora sí guardamos en la base de datos
            usuario.save()
            
            # BONUS UX: Le mostramos al instructor cuál fue la contraseña que se generó
            mensaje = f"¡Aprendiz {usuario.first_name} registrado! Usuario: {usuario.documento} | Clave: {password_generada}"
            messages.success(request, mensaje)
            
            return redirect('inicio_usuario')
        else:
            messages.error(request, "Error al registrar. Por favor verifica los datos.")
    else:
        form = UsuarioForm()

    context = {
        'form': form,
        'titulo': 'Registrar Nuevo Aprendiz',
        'breadcrumbs': [
            {'nombre': 'Ficha', 'url': '#'},
            {'nombre': 'Directorio', 'url': '/usuarios/'}, 
            {'nombre': 'Nuevo Aprendiz', 'url': ''}
        ],
    }
    return render(request, 'aprendices/agregar_aprendiz.html', context)


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
    return render(request, 'aprendices/agregar_aprendiz.html', context)