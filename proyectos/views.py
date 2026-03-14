from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Proyecto, Tarea, DailyScrum, RevisionTecnica
from usuarios.models import Ficha, Usuario

def listar_proyectos(request):
    """Vista principal: Lista de grupos de proyecto de la ficha activa."""
    ficha_id = request.session.get('ficha_activa_id')
    if not ficha_id:
        messages.warning(request, "Selecciona una ficha para gestionar proyectos.")
        return redirect('inicio')

    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)
    # Aquí traerías los proyectos filtrados por ficha
    proyectos = Proyecto.objects.filter(ficha=ficha)

    contexto = {
        'titulo': 'Gestión de Proyectos Scrum',
        'proyectos': proyectos,
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': ''}
        ]
    }
    return render(request, 'proyectos/proyectos.html', contexto)


def nuevo_grupo(request):
    """Vista para crear un nuevo equipo de trabajo."""
    ficha_id = request.session.get('ficha_activa_id')
    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)

    if request.method == 'POST':
        # Lógica para crear el proyecto y asignar integrantes
        nombre = request.POST.get('nombre')
        objetivo = request.POST.get('objetivo')
        scrum_master_id = request.POST.get('scrum_master')
        integrantes_ids = request.POST.getlist('integrantes')

        proyecto = Proyecto.objects.create(
            ficha=ficha,
            nombre=nombre,
            objetivo=objetivo,
            scrum_master_id=scrum_master_id
        )
        proyecto.integrantes.set(integrantes_ids)
        
        messages.success(request, f"Proyecto '{nombre}' creado exitosamente.")
        return redirect('proyectos')

    # Filtramos aprendices para el formulario (ajusta según tu modelo)
    aprendices = Usuario.objects.filter(rol='APRENDIZ') 

    contexto = {
        'titulo': 'Crear Nuevo Grupo',
        'aprendices': aprendices,
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': '/proyectos/'},
            {'nombre': 'Nuevo Grupo', 'url': ''}
        ]
    }
    return render(request, 'proyectos/nuevo-grupo.html', contexto)


def detalles_proyecto(request, proyecto_id):
    """Ficha técnica del proyecto, equipo y bitácora de revisiones."""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    revisiones = RevisionTecnica.objects.filter(proyecto=proyecto).order_by('-fecha')

    contexto = {
        'titulo': f'Detalles: {proyecto.nombre}',
        'proyecto': proyecto,
        'revisiones': revisiones,
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': '/proyectos/'},
            {'nombre': 'Detalles del Proyecto', 'url': ''}
        ]
    }
    return render(request, 'proyectos/detalles.html', contexto)


def tablero_kanban(request, proyecto_id):
    """Tablero ágil con tareas divididas por estado."""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    # LÓGICA PARA CREAR TAREA
    if request.method == 'POST' and request.POST.get('accion') == 'crear_tarea':
        responsable_id = request.POST.get('responsable')
        responsable_obj = Usuario.objects.filter(id=responsable_id).first() if responsable_id else None
        
        Tarea.objects.create(
            proyecto=proyecto,
            nombre=request.POST.get('nombre'),
            descripcion=request.POST.get('descripcion', ''),
            responsable=responsable_obj,
            prioridad=request.POST.get('prioridad', 'Media'),
            estado='To Do' # Entra directamente a la primera columna
        )
        messages.success(request, "Tarea agregada al Sprint.")
        return redirect('tablero_kanban', proyecto_id=proyecto.id)

    # LECTURA DE TAREAS PARA PINTAR LAS COLUMNAS
    tareas = Tarea.objects.filter(proyecto=proyecto)

    contexto = {
        'titulo': 'Tablero Kanban',
        'proyecto': proyecto,
        'todo': tareas.filter(estado='To Do'),
        'doing': tareas.filter(estado='In Progress'),
        'done': tareas.filter(estado='Done'),
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': '/proyectos/'},
            {'nombre': proyecto.nombre, 'url': f'/proyectos/{proyecto.id}/'},
            {'nombre': 'Tablero Kanban', 'url': ''}
        ]
    }
    return render(request, 'proyectos/tablero.html', contexto)


def registrar_daily(request, proyecto_id):
    """Registro del reporte diario por parte del Scrum Master."""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == 'POST':
        # Lógica para guardar el reporte DailyScrum
        DailyScrum.objects.create(
            proyecto=proyecto,
            logros=request.POST.get('logros'),
            planes=request.POST.get('planes'),
            bloqueos=request.POST.get('bloqueos')
        )
        messages.success(request, "Reporte Daily enviado correctamente.")
        return redirect('detalles_proyecto', proyecto_id=proyecto.id)

    contexto = {
        'titulo': 'Registro Daily Scrum',
        'proyecto': proyecto,
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': '/proyectos/'},
            {'nombre': proyecto.nombre, 'url': f'/proyectos/{proyecto.id}/'},
            {'nombre': 'Daily Scrum', 'url': ''}
        ]
    }
    return render(request, 'proyectos/daily.html', contexto)


def registrar_avance(request, proyecto_id):
    """Evaluación técnica realizada por el Instructor."""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == 'POST':
        # Lógica para guardar la revisión técnica
        RevisionTecnica.objects.create(
            proyecto=proyecto,
            instructor=request.user,
            hito=request.POST.get('hito'),
            observaciones=request.POST.get('observaciones'),
            estado_resultado=request.POST.get('estado')
        )
        messages.success(request, "Evaluación de avance guardada.")
        return redirect('detalles_proyecto', proyecto_id=proyecto.id)

    contexto = {
        'titulo': 'Evaluar Avance Técnico',
        'proyecto': proyecto,
        'breadcrumbs': [
            {'nombre': 'Proyectos Scrum', 'url': '/proyectos/'},
            {'nombre': proyecto.nombre, 'url': f'/proyectos/{proyecto.id}/'},
            {'nombre': 'Evaluar Avance', 'url': ''}
        ]
    }
    return render(request, 'proyectos/avance.html', contexto)