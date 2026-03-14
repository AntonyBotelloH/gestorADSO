from django.shortcuts import render, get_object_or_404
from .models import Competencia, ResultadoAprendizaje, ActividadPlaneacion, FaseProyecto
from usuarios.models import Ficha

def inicio_planeacion(request):
    """
    Vista principal: Muestra el cronograma de actividades de la ficha activa.
    """
    codigo_ficha = request.session.get('ficha_activa_id')
    contexto = {'titulo': 'Planeación Pedagógica'}
    
    if codigo_ficha:
        ficha = get_object_or_404(Ficha, codigo_ficha=codigo_ficha)
        # Traemos las actividades de planeación filtradas por la ficha activa
        actividades = ActividadPlaneacion.objects.filter(ficha=ficha).select_related('fase', 'rap', 'instructor')
        
        contexto.update({
            'actividades': actividades,
            'breadcrumbs': [
                {'nombre': 'Inicio', 'url': '/'},
                {'nombre': 'Planeación', 'url': ''}
            ]
        })
    
    return render(request, 'planeacion/inicio_planeacion.html', contexto)

def listar_raps(request):
    """
    Muestra los Resultados de Aprendizaje asociados a las competencias.
    """
    codigo_ficha = request.session.get('ficha_activa_id')
    raps = ResultadoAprendizaje.objects.all().select_related('competencia')
    
    contexto = {
        'titulo': 'Resultados de Aprendizaje',
        'raps': raps,
        'breadcrumbs': [
            {'nombre': 'Inicio', 'url': '/'},
            {'nombre': 'Planeación', 'url': '/planeacion/'},
            {'nombre': 'RAPs', 'url': ''}
        ]
    }
    
    return render(request, 'planeacion/rap_list.html', contexto)

def listar_competencias(request):
    """
    Muestra el listado de competencias técnicas y transversales.
    """
    competencias = Competencia.objects.all()
    
    contexto = {
        'titulo': 'Competencias del Programa',
        'competencias': competencias,
        'breadcrumbs': [
            {'nombre': 'Inicio', 'url': '/'},
            {'nombre': 'Planeación', 'url': '/planeacion/'},
            {'nombre': 'Competencias', 'url': ''}
        ]
    }
    
    return render(request, 'planeacion/competencia_list.html', contexto)