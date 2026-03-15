from django.shortcuts import render

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