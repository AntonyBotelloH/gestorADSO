from django.shortcuts import render
from django.urls import reverse

def inicio(request):
    """Vista de la página principal (Dashboard de Inicio)."""
    context = {
        'titulo': 'Inicio',
        # Opcional: si tu inicio también usa breadcrumbs
        
    }
    return render(request, 'index.html', context)


def configuraciones(request):
    """Vista para la página de Ajustes y Accesibilidad."""
    context = {
        'titulo': 'Configuraciones',
        'breadcrumbs': [
            {'nombre': 'Configuraciones', 'url': ''}
        ]
    }
    return render(request, 'configuraciones.html', context)