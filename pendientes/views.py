from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def listar_pendientes(request):
    """Vista para la gestión de tareas del instructor."""
    context = {
        'titulo': 'Mis Pendientes',
        'breadcrumbs': [
            {'nombre': 'Inicio', 'url': '/'},
            {'nombre': 'Mis Pendientes', 'url': ''}
        ]
    }
    return render(request, 'pendientes/pendientes.html', context)