import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Competencia, ResultadoAprendizaje, ActividadPlaneacion
from usuarios.models import Ficha

def inicio_planeacion(request):
    """Vista principal con el cronograma de la ficha activa."""
    codigo_ficha = request.session.get('ficha_activa_id')
    actividades = []
    
    if codigo_ficha:
        ficha = get_object_or_404(Ficha, codigo_ficha=codigo_ficha)
        actividades = ActividadPlaneacion.objects.filter(ficha=ficha).select_related('fase', 'rap', 'instructor')

    contexto = {
        'titulo': 'Fases y Actividades',
        'actividades': actividades,
        'breadcrumbs': [
            {'nombre': 'Inicio', 'url': '/'},
            {'nombre': 'Planeación', 'url': ''}
        ]
    }
    return render(request, 'planeacion/inicio_planeacion.html', contexto)

def listar_raps(request):
    """Lista todos los Resultados de Aprendizaje."""
    raps = ResultadoAprendizaje.objects.all().select_related('competencia')
    return render(request, 'planeacion/rap_list.html', {
        'titulo': 'Resultados de Aprendizaje',
        'raps': raps,
        'breadcrumbs': [{'nombre': 'Inicio', 'url': '/'}, {'nombre': 'RAPs', 'url': ''}]
    })

def listar_competencias(request):
    """Lista todas las Competencias."""
    competencias = Competencia.objects.all()
    return render(request, 'planeacion/competencia_list.html', {
        'titulo': 'Competencias',
        'competencias': competencias,
        'breadcrumbs': [{'nombre': 'Inicio', 'url': '/'}, {'nombre': 'Competencias', 'url': ''}]
    })

def importar_curriculo(request):
    """Procesa el archivo Excel y puebla la base de datos."""
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        
        try:
            # Leer el Excel usando pandas
            df = pd.read_excel(archivo)
            
            # Validar columnas necesarias
            columnas_requeridas = ['codigo_competencia', 'nombre_competencia', 'duracion', 'descripcion_rap']
            if not all(col in df.columns for col in columnas_requeridas):
                messages.error(request, "El archivo no tiene las columnas requeridas.")
                return redirect('importar_curriculo')

            conteo_raps = 0
            
            for _, row in df.iterrows():
                # 1. Crear o actualizar Competencia (update_or_create evita duplicados)
                competencia, created = Competencia.objects.update_or_create(
                    codigo=str(row['codigo_competencia']).strip(),
                    defaults={
                        'nombre': str(row['nombre_competencia']).strip(),
                        'duracion_horas': int(row['duracion'])
                    }
                )
                
                # 2. Crear el RAP si no existe para esa competencia
                rap, rap_created = ResultadoAprendizaje.objects.get_or_create(
                    competencia=competencia,
                    descripcion=str(row['descripcion_rap']).strip()
                )
                
                if rap_created:
                    conteo_raps += 1
            
            messages.success(request, f"Proceso terminado. Se crearon/actualizaron {conteo_raps} Resultados de Aprendizaje.")
            return redirect('listar_raps')

        except Exception as e:
            messages.error(request, f"Error crítico al leer el Excel: {e}")
            return redirect('importar_curriculo')

    return render(request, 'planeacion/importar.html', {'titulo': 'Importar Diseño Curricular'})