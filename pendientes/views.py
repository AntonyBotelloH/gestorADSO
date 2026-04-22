from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Pendiente
from .forms import PendienteForm

@login_required
def listar_pendientes(request):
    """Vista para la gestión de tareas del instructor."""
    
    # Procesar formulario para crear una nueva tarea
    if request.method == 'POST' and 'descripcion' in request.POST:
        form = PendienteForm(request.POST)
        if form.is_valid():
            pendiente = form.save(commit=False)
            pendiente.instructor = request.user
            pendiente.save()
            messages.success(request, "Tarea agregada a tus pendientes.")
            return redirect('listar_pendientes')
        else:
            messages.error(request, "Error al crear la tarea. Revisa los datos.")
    else:
        form = PendienteForm()

    # Obtener las listas de pendientes para el instructor logueado
    pendientes_activos = Pendiente.objects.filter(instructor=request.user, completada=False)
    pendientes_completados = Pendiente.objects.filter(instructor=request.user, completada=True)
    
    total_pendientes = pendientes_activos.count() + pendientes_completados.count()
    porcentaje_completado = 0
    if total_pendientes > 0:
        porcentaje_completado = int((pendientes_completados.count() / total_pendientes) * 100)

    context = {
        'titulo': 'Mis Pendientes',
        'form': form,
        'pendientes_activos': pendientes_activos,
        'pendientes_completados': pendientes_completados,
        'porcentaje_completado': porcentaje_completado,
        'breadcrumbs': [
            {'nombre': 'Mis Pendientes', 'url': ''}
        ]
    }
    return render(request, 'pendientes/pendientes.html', context)

@login_required
def marcar_completada(request, pendiente_id):
    """Marca o desmarca una tarea como completada."""
    if request.method == 'POST':
        # Buscamos la tarea, asegurándonos que le pertenece al usuario logueado
        pendiente = get_object_or_404(Pendiente, id=pendiente_id, instructor=request.user)
        
        # Invertimos el estado booleano
        pendiente.completada = not pendiente.completada
        pendiente.save()
        
        # Damos feedback al usuario
        if pendiente.completada:
            messages.success(request, f"¡Tarea '{pendiente.descripcion[:20]}...' completada!")
        else:
            messages.info(request, "La tarea se ha marcado como pendiente de nuevo.")
            
    # Redirigimos siempre a la lista principal
    return redirect('listar_pendientes')

@login_required
def eliminar_pendiente(request, pendiente_id):
    """Elimina una tarea permanentemente."""
    if request.method == 'POST':
        pendiente = get_object_or_404(Pendiente, id=pendiente_id, instructor=request.user)
        descripcion_corta = pendiente.descripcion[:20]
        pendiente.delete()
        messages.warning(request, f"La tarea '{descripcion_corta}...' fue eliminada.")
        
    return redirect('listar_pendientes')

@login_required
def limpiar_completadas(request):
    """Elimina TODAS las tareas que ya han sido completadas por el usuario."""
    if request.method == 'POST':
        # Buscamos y contamos cuántas se van a borrar
        completadas = Pendiente.objects.filter(instructor=request.user, completada=True)
        count = completadas.count()
        
        if count > 0:
            completadas.delete()
            messages.success(request, f"Se eliminaron {count} tareas completadas de tu historial.")
        else:
            messages.info(request, "No tenías tareas completadas para limpiar.")

    return redirect('listar_pendientes')