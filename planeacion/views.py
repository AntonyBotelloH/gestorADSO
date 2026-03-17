import pandas as pd
import re  
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from planeacion.forms import ActividadPlaneacionForm
from .models import Competencia, ResultadoAprendizaje, ActividadPlaneacion
from usuarios.models import Ficha

def inicio_planeacion(request):
    """Vista principal con el cronograma de la ficha activa."""
    codigo_ficha = request.session.get('ficha_activa_id')
    
    # Inicializar variables por defecto
    actividades = []
    total_actividades = 0
    act_en_curso = 0
    act_terminadas = 0
    act_pendientes = 0
    
    if codigo_ficha:
        ficha = get_object_or_404(Ficha, codigo_ficha=codigo_ficha)
        # prefetch_related es OBLIGATORIO para los campos ManyToMany (raps) para no saturar la BD
        actividades = ActividadPlaneacion.objects.filter(ficha=ficha).select_related('fase', 'instructor').prefetch_related('raps').order_by('fecha_inicio')
        
        # Cálculos para el Dashboard (Tarjetas superiores)
        total_actividades = actividades.count()
        act_en_curso = actividades.filter(estado='En Curso').count()
        act_terminadas = actividades.filter(estado='Terminada').count()
        act_pendientes = actividades.filter(estado='Pendiente').count()

    contexto = {
        'titulo': 'Fases y Actividades',
        'actividades': actividades,
        'total_actividades': total_actividades,
        'act_en_curso': act_en_curso,
        'act_terminadas': act_terminadas,
        'act_pendientes': act_pendientes,
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
    """Procesa el archivo Excel original de Planeación de SOFIA Plus automáticamente."""
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        
        try:
            # 1. Leer el Excel saltando el encabezado institucional
            # Buscamos dinámicamente la fila de encabezados por si SOFIA cambia el formato
            df_temp = pd.read_excel(archivo, nrows=20, header=None)
            header_idx = 14 # Fila por defecto donde suele empezar en SOFIA
            for i, row in df_temp.iterrows():
                # Si encontramos estas palabras clave, esa es la fila de encabezados reales
                if 'COMPETENCIA' in str(row.values).upper() or 'RESULTADOS DE APRENDIZAJE' in str(row.values).upper():
                    header_idx = i
                    break
            
            # Leer el dataframe real usando la fila encontrada como encabezado
            df = pd.read_excel(archivo, header=header_idx)
            
            # 2. Identificar columnas dinámicamente (SOFIA a veces cambia ligeramente los nombres)
            col_comp = [c for c in df.columns if 'COMPETENCIA' in str(c).upper()][0]
            col_rap = [c for c in df.columns if 'RESULTADOS DE APRENDIZAJE' in str(c).upper()][0]
            
            # Intentar encontrar columna de duración
            col_duracion = [c for c in df.columns if 'DURACIÓN' in str(c).upper() and 'APRENDIZAJE' in str(c).upper()]
            col_duracion = col_duracion[0] if col_duracion else None

            # 3. Limpieza: Rellenar celdas combinadas hacia abajo y quitar filas sin RAP
            df[col_comp] = df[col_comp].ffill()
            df = df.dropna(subset=[col_rap])

            conteo_raps = 0
            
            for _, row in df.iterrows():
                comp_raw = str(row[col_comp]).strip()
                rap_desc = str(row[col_rap]).strip()
                
                # Omitir filas que sean encabezados repetidos, subtítulos o basura
                if comp_raw.upper() == 'COMPETENCIA' or rap_desc.lower() == 'nan' or len(rap_desc) < 10:
                    continue

                # 4. Separar Código y Nombre usando Regex (Ej: "220501096 - Desarrollar...")
                match = re.match(r'^(\d+)\s*[-]*\s*(.+)$', comp_raw)
                if match:
                    codigo_comp = match.group(1)
                    nombre_comp = match.group(2)
                else:
                    # Si no tiene código numérico visible, generamos un identificador temporal seguro
                    codigo_comp = str(abs(hash(comp_raw)))[:8] 
                    nombre_comp = comp_raw
                
                # Obtener duración (limpiando textos)
                duracion = 0
                if col_duracion:
                    val_dur = str(row[col_duracion]).strip()
                    nums = re.findall(r'\d+', val_dur)
                    if nums:
                        duracion = int(nums[0])

                # 5. Guardar o actualizar en Base de Datos
                competencia, _ = Competencia.objects.update_or_create(
                    codigo=codigo_comp,
                    defaults={
                        'nombre': nombre_comp[:150],
                        'duracion_horas': duracion
                    }
                )
                
                rap, rap_created = ResultadoAprendizaje.objects.get_or_create(
                    competencia=competencia,
                    descripcion=rap_desc
                )
                
                if rap_created:
                    conteo_raps += 1
            
            messages.success(request, f"¡Importación Exitosa! Se procesó el archivo de SOFIA Plus y se extrajeron {conteo_raps} Resultados de Aprendizaje.")
            return redirect('listar_raps')

        except Exception as e:
            messages.error(request, f"Error al procesar el archivo. Asegúrate de que es el reporte de Planeación de SOFIA Plus. Detalle: {e}")
            return redirect('importar_curriculo')

    return render(request, 'planeacion/importar.html', {
        'titulo': 'Importar Diseño Curricular',
        'breadcrumbs': [
            {'nombre': 'Inicio', 'url': '/'}, 
            {'nombre': 'Planeación', 'url': '/planeacion/'},
            {'nombre': 'Importar', 'url': ''}
        ]
    })
    


def crear_actividad(request):
    """Crea una nueva actividad para la ficha activa en sesión."""
    # Obtenemos el ID de la ficha desde la sesión
    ficha_id = request.session.get('ficha_activa_id')
    
    if not ficha_id:
        messages.error(request, "Primero debes seleccionar una ficha de formación.")
        return redirect('inicio_planeacion')

    ficha = get_object_or_404(Ficha, codigo_ficha=ficha_id)

    if request.method == 'POST':
        form = ActividadPlaneacionForm(request.POST)
        if form.is_valid():
            # Guardamos con commit=False para asignar la ficha manualmente
            actividad = form.save(commit=False)
            actividad.ficha = ficha
            actividad.save()
            
            # Como raps es ManyToMany, debemos guardar las relaciones después del .save()
            form.save_m2m()
            
            messages.success(request, "Actividad programada correctamente en el cronograma.")
            return redirect('inicio_planeacion')
    else:
        # Al crear, podemos filtrar los RAPs si quisiéramos, 
        # por ahora cargamos el formulario limpio
        form = ActividadPlaneacionForm()

    return render(request, 'planeacion/actividad_form.html', {
        'form': form,
        'titulo': 'Nueva Actividad de Proyecto',
        'breadcrumbs': [
            {'nombre': 'Inicio', 'url': '/'},
            {'nombre': 'Planeación', 'url': '/planeacion/'},
            {'nombre': 'Nueva Actividad', 'url': ''}
        ]
    })

def editar_actividad(request, pk):
    """Edita una actividad existente."""
    actividad = get_object_or_404(ActividadPlaneacion, pk=pk)
    
    if request.method == 'POST':
        form = ActividadPlaneacionForm(request.POST, instance=actividad)
        if form.is_valid():
            form.save()
            messages.success(request, "Actividad actualizada correctamente.")
            return redirect('inicio_planeacion')
    else:
        form = ActividadPlaneacionForm(instance=actividad)

    return render(request, 'planeacion/actividad_form.html', {
        'form': form,
        'titulo': 'Editar Actividad',
        'breadcrumbs': [
            {'nombre': 'Inicio', 'url': '/'},
            {'nombre': 'Planeación', 'url': '/planeacion/'},
            {'nombre': 'Editar', 'url': ''}
        ]
    })