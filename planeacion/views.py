import pandas as pd
import re
import io
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from usuarios.decorators import rol_requerido

from planeacion.forms import ActividadPlaneacionForm, CompetenciaForm, ResultadoAprendizajeForm
from .models import Competencia, ResultadoAprendizaje, ActividadPlaneacion
from usuarios.models import Ficha

@login_required
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
        # 'fase' es CharField con choices, no es relación, por eso no debe ir en select_related
        actividades = ActividadPlaneacion.objects.filter(ficha=ficha).select_related('instructor').prefetch_related('raps').order_by('fecha_inicio')
        
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
            
            {'nombre': 'Planeación', 'url': ''}
        ]
    }
    return render(request, 'planeacion/inicio_planeacion.html', contexto)
@login_required
def listar_raps(request):
    """Lista todos los Resultados de Aprendizaje."""
    raps = ResultadoAprendizaje.objects.all().select_related('competencia')
    ficha_activa_id = request.session.get('ficha_activa_id')
    ficha_activa = None
    if ficha_activa_id:
        ficha_activa = Ficha.objects.filter(codigo_ficha=ficha_activa_id).first()

    return render(request, 'planeacion/rap_list.html', {
        'titulo': 'Resultados de Aprendizaje',
        'raps': raps,
        'ficha_activa': ficha_activa,
        'breadcrumbs': [ {'nombre': 'RAPs', 'url': ''}]
    })

@login_required
def listar_competencias(request):
    """Lista todas las Competencias."""
    competencias = Competencia.objects.all().order_by('codigo')
    ficha_activa_id = request.session.get('ficha_activa_id')
    ficha_activa = None
    if ficha_activa_id:
        ficha_activa = Ficha.objects.filter(codigo_ficha=ficha_activa_id).first()
    
    return render(request, 'planeacion/competencia_list.html', {
        'titulo': 'Competencias',
        'competencias': competencias,
        'ficha_activa': ficha_activa,
        'breadcrumbs': [ {'nombre': 'Competencias', 'url': ''}]
    })


@login_required
@rol_requerido('INSTRUCTOR', 'Admin')
def crear_competencia(request):
    """Crea una competencia nueva."""
    if request.method == 'POST':
        form = CompetenciaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Competencia creada correctamente.')
            return redirect('listar_competencias')
    else:
        form = CompetenciaForm()

    return render(request, 'planeacion/competencia_form.html', {
        'titulo': 'Nueva Competencia',
        'form': form,
        'breadcrumbs': [
            {'nombre': 'Planeación', 'url': '/planeacion/'},
            {'nombre': 'Competencias', 'url': '/planeacion/competencias/'},
            {'nombre': 'Nueva', 'url': ''}
        ]
    })


@login_required
@rol_requerido('INSTRUCTOR', 'Admin')
def editar_competencia(request, pk):
    competencia = get_object_or_404(Competencia, pk=pk)
    if request.method == 'POST':
        form = CompetenciaForm(request.POST, instance=competencia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Competencia actualizada correctamente.')
            return redirect('listar_competencias')
    else:
        form = CompetenciaForm(instance=competencia)

    return render(request, 'planeacion/competencia_form.html', {
        'titulo': 'Editar Competencia',
        'form': form,
        'breadcrumbs': [
            {'nombre': 'Planeación', 'url': '/planeacion/'},
            {'nombre': 'Competencias', 'url': '/planeacion/competencias/'},
            {'nombre': 'Editar', 'url': ''}
        ]
    })


@login_required
@rol_requerido('INSTRUCTOR', 'Admin')
def eliminar_competencia(request, pk):
    competencia = get_object_or_404(Competencia, pk=pk)
    competencia.delete()
    messages.success(request, 'Competencia eliminada correctamente.')
    return redirect('listar_competencias')


@login_required
@rol_requerido('INSTRUCTOR', 'Admin')
def crear_rap(request):
    if request.method == 'POST':
        form = ResultadoAprendizajeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Resultado de Aprendizaje creado correctamente.')
            return redirect('listar_raps')
    else:
        form = ResultadoAprendizajeForm()

    return render(request, 'planeacion/rap_form.html', {
        'titulo': 'Nuevo Resultado de Aprendizaje',
        'form': form,
        'breadcrumbs': [
            {'nombre': 'Planeación', 'url': '/planeacion/'},
            {'nombre': 'RAPs', 'url': '/planeacion/raps/'},
            {'nombre': 'Nuevo', 'url': ''}
        ]
    })


@login_required
@rol_requerido('INSTRUCTOR', 'Admin')
def editar_rap(request, pk):
    rap = get_object_or_404(ResultadoAprendizaje, pk=pk)
    if request.method == 'POST':
        form = ResultadoAprendizajeForm(request.POST, instance=rap)
        if form.is_valid():
            form.save()
            messages.success(request, 'Resultado de Aprendizaje actualizado correctamente.')
            return redirect('listar_raps')
    else:
        form = ResultadoAprendizajeForm(instance=rap)

    return render(request, 'planeacion/rap_form.html', {
        'titulo': 'Editar Resultado de Aprendizaje',
        'form': form,
        'breadcrumbs': [
            {'nombre': 'Planeación', 'url': '/planeacion/'},
            {'nombre': 'RAPs', 'url': '/planeacion/raps/'},
            {'nombre': 'Editar', 'url': ''}
        ]
    })


@login_required
@rol_requerido('INSTRUCTOR', 'Admin')
def eliminar_rap(request, pk):
    rap = get_object_or_404(ResultadoAprendizaje, pk=pk)
    rap.delete()
    messages.success(request, 'Resultado de Aprendizaje eliminado correctamente.')
    return redirect('listar_raps')

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
            
            {'nombre': 'Planeación', 'url': '/planeacion/'},
            {'nombre': 'Editar', 'url': ''}
        ]
    })


def detalle_actividad(request, pk):
    """Muestra los datos de una actividad."""
    actividad = get_object_or_404(ActividadPlaneacion, pk=pk)
    return render(request, 'planeacion/actividad_detalle.html', {
        'actividad': actividad,
        'titulo': 'Detalle de Actividad',
        'breadcrumbs': [
            {'nombre': 'Planeación', 'url': '/planeacion/'},
            {'nombre': 'Cronograma', 'url': '/planeacion/'},
            {'nombre': 'Detalle', 'url': ''}
        ]
    })

def exportar_planeacion_excel(request):
    """Exporta el cronograma de la ficha activa a un archivo Excel."""
    codigo_ficha = request.session.get('ficha_activa_id')
    if not codigo_ficha:
        messages.error(request, "No hay una ficha activa para exportar.")
        return redirect('inicio_planeacion')

    ficha = get_object_or_404(Ficha, codigo_ficha=codigo_ficha)
    
    # Usamos prefetch_related para optimizar la consulta de RAPs y Competencias
    actividades = ActividadPlaneacion.objects.filter(ficha=ficha).select_related(
        'instructor'
    ).prefetch_related(
        'raps', 'raps__competencia'
    ).order_by('fecha_inicio')

    if not actividades.exists():
        messages.warning(request, "No hay actividades en la planeación para exportar.")
        return redirect('inicio_planeacion')

    # Preparamos los datos para el DataFrame
    data = []
    for act in actividades:
        # Concatenamos los RAPs y competencias
        raps_str = "\n".join([rap.descripcion for rap in act.raps.all()])
        # Usamos un set para evitar competencias duplicadas si varios RAPs son de la misma
        competencias_set = {rap.competencia.nombre for rap in act.raps.all()}
        competencias_str = "\n".join(list(competencias_set))

        data.append({
            'FASE': act.fase if act.fase else '',
            'ACTIVIDAD DE PROYECTO': act.actividad_proyecto,
            'RESULTADOS DE APRENDIZAJE': raps_str,
            'COMPETENCIA': competencias_str,
            'INSTRUCTOR': act.instructor.get_full_name() if act.instructor else 'No asignado',
            'FECHA DE INICIO': act.fecha_inicio,
            'FECHA DE FIN': act.fecha_fin,
        })

    # Crear DataFrame y el archivo Excel en memoria
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'Planeacion {ficha.codigo_ficha}', index=False)
        # Opcional: Auto-ajustar el ancho de las columnas
        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets[f'Planeacion {ficha.codigo_ficha}'].column_dimensions[chr(65 + col_idx)].width = column_length + 2

    output.seek(0)

    # Preparar la respuesta HTTP
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="Plan_C1_{ficha.codigo_ficha}.xlsx"'

    return response