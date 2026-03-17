from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from usuarios.decorators import rol_requerido # Asegúrate de que la ruta sea correcta
from .models import Proyecto, Tarea, DailyScrum, RevisionTecnica
from usuarios.models import Ficha, Usuario

@login_required
def listar_proyectos(request):
    """Vista principal: Lista de grupos de proyecto de la ficha activa."""
    ficha_id = request.session.get('ficha_activa_id')
    if not ficha_id:
        messages.warning(request, "Selecciona una ficha para gestionar proyectos.")
        return redirect('inicio')

    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)
    proyectos = Proyecto.objects.filter(ficha=ficha)

    contexto = {
        'proyectos': proyectos,
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': ''}
        ]
    }
    return render(request, 'proyectos/proyectos.html', contexto)

@login_required
@rol_requerido('VOCERO', 'INSTRUCTOR', 'Admin')
def nuevo_grupo(request):
    """Vista para crear un nuevo equipo de trabajo con validación de fecha."""
    ficha_id = request.session.get('ficha_activa_id')
    if not ficha_id:
        messages.warning(request, "Selecciona una ficha primero.")
        return redirect('inicio')
        
    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        objetivo = request.POST.get('objetivo')
        scrum_master_id = request.POST.get('scrum_master')
        integrantes_ids = request.POST.getlist('integrantes')
        fecha_inicio = request.POST.get('fecha_inicio') # Capturamos la fecha del formulario

        try:
            # CORRECCIÓN: Se incluye fecha_inicio para evitar IntegrityError
            proyecto = Proyecto.objects.create(
                ficha=ficha,
                nombre=nombre,
                objetivo=objetivo,
                scrum_master_id=scrum_master_id,
                fecha_inicio=fecha_inicio,
                estado='Al Día'
            )
            if integrantes_ids:
                proyecto.integrantes.set(integrantes_ids)
            
            messages.success(request, f"¡Equipo '{nombre}' creado y activado!")
            return redirect('proyectos')
        except Exception as e:
            messages.error(request, f"Error al guardar: {e}")

    # Filtramos aprendices de la ficha activa para el equipo
    aprendices = Usuario.objects.filter(rol__in=['APRENDIZ', 'VOCERO'], ficha=ficha).order_by('last_name')


    contexto = {
        'aprendices': aprendices,
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': reverse('proyectos')},
            {'nombre': 'Nuevo Grupo', 'url': ''}
        ]
    }
    return render(request, 'proyectos/nuevo-grupo.html', contexto)

@login_required
def detalles_proyecto(request, proyecto_id):
    """Ficha técnica del proyecto, equipo y bitácora de revisiones."""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    revisiones = RevisionTecnica.objects.filter(proyecto=proyecto).order_by('-fecha')

    contexto = {
        'proyecto': proyecto,
        'revisiones': revisiones,
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': reverse('proyectos')},
            {'nombre': 'Detalles del Proyecto', 'url': ''}
        ]
    }
    return render(request, 'proyectos/detalles.html', contexto)

@login_required
def tablero_kanban(request, proyecto_id):
    """Tablero ágil con gestión de tareas por estado."""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    if request.method == 'POST' and request.POST.get('accion') == 'crear_tarea':
        responsable_id = request.POST.get('responsable')
        responsable_obj = Usuario.objects.filter(id=responsable_id).first()
        
        Tarea.objects.create(
            proyecto=proyecto,
            nombre=request.POST.get('nombre'),
            descripcion=request.POST.get('descripcion', ''),
            responsable=responsable_obj,
            prioridad=request.POST.get('prioridad', 'Media'),
            estado='To Do'
        )
        messages.success(request, "Tarea agregada al Sprint Backlog.")
        return redirect('tablero_kanban', proyecto_id=proyecto.id)

    tareas = Tarea.objects.filter(proyecto=proyecto)

    contexto = {
        'proyecto': proyecto,
        'todo': tareas.filter(estado='To Do'),
        'doing': tareas.filter(estado='In Progress'),
        'done': tareas.filter(estado='Done'),
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': reverse('proyectos')},
            {'nombre': proyecto.nombre, 'url': reverse('detalles_proyecto', args=[proyecto.id])},
            {'nombre': 'Tablero Kanban', 'url': ''}
        ]
    }
    return render(request, 'proyectos/tablero.html', contexto)

@login_required
def cambiar_estado_tarea(request, tarea_id):
    """Mueve una tarea de columna en el tablero."""
    if request.method == 'POST':
        tarea = get_object_or_404(Tarea, id=tarea_id)
        nuevo_estado = request.POST.get('nuevo_estado')
        
        if nuevo_estado in ['To Do', 'In Progress', 'Done']:
            tarea.estado = nuevo_estado
            tarea.save()
            messages.success(request, f"Tarea actualizada a {nuevo_estado}")
        
        return redirect('tablero_kanban', proyecto_id=tarea.proyecto.id)
    return redirect('proyectos')

@login_required
def registrar_daily(request, proyecto_id):
    """Reporte diario Scrum del equipo."""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == 'POST':
        DailyScrum.objects.create(
            proyecto=proyecto,
            logros=request.POST.get('logros'),
            planes=request.POST.get('planes'),
            bloqueos=request.POST.get('bloqueos')
        )
        messages.success(request, "¡Daily Report enviado!")
        return redirect('detalles_proyecto', proyecto_id=proyecto.id)

    contexto = {
        'proyecto': proyecto,
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': reverse('proyectos')},
            {'nombre': proyecto.nombre, 'url': reverse('detalles_proyecto', args=[proyecto.id])},
            {'nombre': 'Daily Scrum', 'url': ''}
        ]
    }
    return render(request, 'proyectos/daily.html', contexto)

@login_required
@rol_requerido('INSTRUCTOR', 'Admin')
def registrar_avance(request, proyecto_id):
    """Evaluación de hito realizada por el instructor."""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == 'POST':
        RevisionTecnica.objects.create(
            proyecto=proyecto,
            instructor=request.user,
            hito=request.POST.get('hito'),
            observaciones=request.POST.get('observaciones'),
            estado_resultado=request.POST.get('estado')
        )
        # Actualizamos también el estado general del proyecto
        proyecto.estado = request.POST.get('estado')
        proyecto.save()

        messages.success(request, "Evaluación técnica guardada exitosamente.")
        return redirect('detalles_proyecto', proyecto_id=proyecto.id)

    contexto = {
        'proyecto': proyecto,
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': reverse('proyectos')},
            {'nombre': proyecto.nombre, 'url': reverse('detalles_proyecto', args=[proyecto.id])},
            {'nombre': 'Evaluar Avance', 'url': ''}
        ]
    }
    return render(request, 'proyectos/avance.html', contexto)