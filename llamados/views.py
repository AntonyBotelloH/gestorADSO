from django.shortcuts import render

def listar_llamados(request):
    context = {
        'titulo': 'Control Disciplinario',
        'breadcrumbs': [{'nombre': 'Llamados de Atención', 'url': ''}]
    }
    return render(request, 'llamados/llamados.html', context)

def detalle_llamado(request):
    context = {
        'titulo': 'Expediente Disciplinario',
        'breadcrumbs': [
            {'nombre': 'Llamados', 'url': '/llamados/'},
            {'nombre': 'Detalle', 'url': ''}
        ]
    }
    return render(request, 'llamados/detalle.html', context)

def estrategias(request):
    context = {
        'titulo': 'Estrategias Pedagógicas',
        'breadcrumbs': [
            {'nombre': 'Llamados', 'url': '/llamados/'},
            {'nombre': 'Estrategias', 'url': ''}
        ]
    }
    return render(request, 'llamados/estrategias.html', context)

def estadisticas(request):
    context = {
        'titulo': 'Estadísticas Disciplinarias',
        'breadcrumbs': [
            {'nombre': 'Llamados', 'url': '/llamados/'},
            {'nombre': 'Estadísticas', 'url': ''}
        ]
    }
    return render(request, 'llamados/estadisticas.html', context)