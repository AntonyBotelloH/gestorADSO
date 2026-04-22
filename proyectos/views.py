from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from usuarios.decorators import rol_requerido # Asegúrate de que la ruta sea correcta
# NUEVO: Importamos Sprint
from .models import Proyecto, Tarea, DailyScrum, RevisionTecnica, Sprint
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
        'titulo': 'Proyectos Scrum',
        'proyectos': proyectos,
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': ''}
        ]
    }
    return render(request, 'proyectos/proyectos.html', contexto)

@login_required
@rol_requerido('VOCERO', 'INSTRUCTOR', 'ADMIN')
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
        fecha_inicio = request.POST.get('fecha_inicio') 

        try:
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

    aprendices = Usuario.objects.filter(rol__in=['APRENDIZ', 'VOCERO'], ficha=ficha).order_by('last_name')

    contexto = {
        'titulo': 'Crear Nuevo Grupo Scrum',
        'aprendices': aprendices,
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': reverse('proyectos')},
            {'nombre': 'Nuevo Grupo', 'url': ''}
        ]
    }
    return render(request, 'proyectos/nuevo-grupo.html', contexto)

@login_required
def crear_sprint(request, proyecto_id):
    """Crea y activa un nuevo Sprint desde el modal de la ficha del proyecto."""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    # Seguridad: Solo el Scrum Master o Instructor/Admin pueden crear sprints
    if request.user != proyecto.scrum_master and request.user.rol not in ['INSTRUCTOR', 'ADMIN']:
        messages.error(request, "Acceso denegado: Solo el Scrum Master puede planificar Sprints.")
        return redirect('detalles_proyecto', proyecto_id=proyecto.id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        objetivo = request.POST.get('objetivo')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        
        # Opcional pero recomendado: Si se crea uno nuevo, asumimos que el anterior terminó
        # Descomenta la siguiente línea si quieres que se auto-completen los anteriores:
        # Sprint.objects.filter(proyecto=proyecto, estado='Activo').update(estado='Completado')

        Sprint.objects.create(
            proyecto=proyecto,
            nombre=nombre,
            objetivo=objetivo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado='Activo', # Lo dejamos activo de una vez
            scrum_master=proyecto.scrum_master
        )
        messages.success(request, f"¡{nombre} planificado y activado exitosamente!")
        
    return redirect('detalles_proyecto', proyecto_id=proyecto.id)

@login_required
def detalles_proyecto(request, proyecto_id):
    """Ficha técnica del proyecto, equipo y bitácora de revisiones."""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == 'POST':
        scrum_master_id = request.POST.get('scrum_master')
        if scrum_master_id:
            nuevo_scrum_master = get_object_or_404(Usuario, id=scrum_master_id)
            proyecto.scrum_master = nuevo_scrum_master
            proyecto.save()
            messages.success(request, f"Se ha asignado a {nuevo_scrum_master.get_full_name()} como nuevo Scrum Master.")
        return redirect('detalles_proyecto', proyecto_id=proyecto.id)

    revisiones = RevisionTecnica.objects.filter(proyecto=proyecto).order_by('-fecha')
    dailies = DailyScrum.objects.filter(proyecto=proyecto).order_by('-id')
    
    # NUEVO: Traemos los Sprints para mostrarlos en la vista de detalles
    sprints = Sprint.objects.filter(proyecto=proyecto).order_by('-fecha_inicio')
    
    contexto = {
        'titulo': f'Detalles del Proyecto: {proyecto.nombre}',
        'proyecto': proyecto,
        'revisiones': revisiones,
        'dailies': dailies,
        'sprints': sprints, # Pasamos los sprints al HTML
        'integrantes': proyecto.integrantes.all(),
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
    sprint_activo = Sprint.objects.filter(proyecto=proyecto, estado='Activo').first()
    
    if request.method == 'POST' and request.POST.get('accion') == 'crear_tarea':
        responsable_id = request.POST.get('responsable')
        responsable_obj = Usuario.objects.filter(id=responsable_id).first()
        
        Tarea.objects.create(
            proyecto=proyecto,
            sprint=sprint_activo, # NUEVO: Se enlaza al sprint activo (si hay uno)
            nombre=request.POST.get('nombre'),
            descripcion=request.POST.get('descripcion', ''),
            responsable=responsable_obj,
            prioridad=request.POST.get('prioridad', 'Media'),
            estado='To Do'
        )
        if sprint_activo:
            messages.success(request, f"Tarea agregada al Sprint Backlog de {sprint_activo.nombre}.")
        else:
            messages.warning(request, "Tarea agregada al Product Backlog (No hay Sprint activo).")
            
        return redirect('tablero_kanban', proyecto_id=proyecto.id)

    # NUEVO: Filtramos solo las tareas del Sprint Activo. Si no hay sprint, mostramos el backlog completo.
    if sprint_activo:
        tareas = Tarea.objects.filter(proyecto=proyecto, sprint=sprint_activo)
    else:
        tareas = Tarea.objects.filter(proyecto=proyecto, sprint__isnull=True)

    contexto = {
        'titulo': f'Tablero Kanban - {proyecto.nombre}',
        'proyecto': proyecto,
        'sprint_activo': sprint_activo,
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
@rol_requerido('VOCERO', 'INSTRUCTOR', 'ADMIN')
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
    # Buscamos si hay un Sprint activo para enlazar el Daily
    sprint_activo = Sprint.objects.filter(proyecto=proyecto, estado='Activo').first()

    if request.user != proyecto.scrum_master and request.user.rol not in ['INSTRUCTOR', 'ADMIN']:
        messages.error(request, "Acceso denegado: Solo el Scrum Master asignado al equipo puede registrar el Daily Scrum.")
        return redirect('detalles_proyecto', proyecto_id=proyecto.id)

    if request.method == 'POST':
        DailyScrum.objects.create(
            proyecto=proyecto,
            sprint=sprint_activo, # NUEVO: Enlazamos al sprint actual
            logros=request.POST.get('logros'),
            planes=request.POST.get('planes'),
            bloqueos=request.POST.get('bloqueos')
        )
        messages.success(request, "¡Daily Report enviado!")
        return redirect('detalles_proyecto', proyecto_id=proyecto.id)

    contexto = {
        'titulo': f'Registrar Daily Scrum - {proyecto.nombre}',
        'proyecto': proyecto,
        'sprint_activo': sprint_activo,
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': reverse('proyectos')},
            {'nombre': proyecto.nombre, 'url': reverse('detalles_proyecto', args=[proyecto.id])},
            {'nombre': 'Daily Scrum', 'url': ''}
        ]
    }
    return render(request, 'proyectos/daily.html', contexto)

@login_required
@rol_requerido('INSTRUCTOR', 'ADMIN')
def registrar_avance(request, proyecto_id):
    """Evaluación de hito realizada por el instructor (Sprint Review)."""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    # NUEVO: Buscamos únicamente el sprint que esté activo en este momento
    sprint_activo = Sprint.objects.filter(proyecto=proyecto, estado='Activo').first()

    if request.method == 'POST':
        RevisionTecnica.objects.create(
            proyecto=proyecto,
            instructor=request.user,
            sprint_evaluado=sprint_activo, # Se asigna directo desde el backend (Más seguro)
            observaciones=request.POST.get('observaciones'),
            estado_resultado=request.POST.get('estado')
        )
        
        # Si el resultado es Atrasado, afectamos el proyecto completo
        proyecto.estado = request.POST.get('estado')
        proyecto.save()

        messages.success(request, "Evaluación técnica guardada exitosamente.")
        return redirect('detalles_proyecto', proyecto_id=proyecto.id)

    contexto = {
        'titulo': f'Evaluar Avance: {proyecto.nombre}',
        'proyecto': proyecto,
        'sprint_activo': sprint_activo, # Pasamos solo el sprint en curso al HTML
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': reverse('proyectos')},
            {'nombre': proyecto.nombre, 'url': reverse('detalles_proyecto', args=[proyecto.id])},
            {'nombre': 'Evaluar Avance', 'url': ''}
        ]
    }
    return render(request, 'proyectos/avance.html', contexto)

@login_required
@rol_requerido('INSTRUCTOR')
def marcar_revision_aplicada(request, revision_id):
    """Permite al instructor marcar una evaluación técnica como 'Corregida' o 'Aplicada'."""
    revision = get_object_or_404(RevisionTecnica, id=revision_id)
    proyecto = revision.proyecto

    # Seguridad: Solo el Instructor puede marcarlo como resuelto
    if request.user.rol == 'INSTRUCTOR':
        revision.aplicado = True
        revision.save()
        messages.success(request, "¡Excelente! Has marcado las observaciones técnicas como aplicadas.")
    else:
        messages.error(request, "Solo un instructor puede realizar esta acción.")
        
    return redirect('detalles_proyecto', proyecto_id=proyecto.id)