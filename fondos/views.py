from django.shortcuts import render
from django.db.models import Sum
from .models import Fondo, ConceptoFondo
# Importamos el modelo Usuario desde tu aplicación 'usuarios'
from usuarios.models import Usuario 

def inicio_fondo(request):
    """
    Controlador principal del Dashboard Financiero de la ficha.
    """
    
    # ==========================================
    # 1. CÁLCULOS PARA LAS TARJETAS SUPERIORES
    # ==========================================
    
    # Caja Real: Sumamos solo los aportes que tienen estado 'PAGADO'
    caja_real = Fondo.objects.filter(estado_pago='PAGADO').aggregate(total=Sum('valor'))['total'] or 0
    
    # Cartera (Por Cobrar): Sumamos lo que está 'PENDIENTE' o en 'MORA'
    cartera = Fondo.objects.filter(estado_pago__in=['PENDIENTE', 'MORA']).aggregate(total=Sum('valor'))['total'] or 0
    
    # Meta de Salida Técnica (Puedes cambiar este valor o luego volverlo una tabla en la BD)
    meta_total = 250000 
    # Calculamos el porcentaje automáticamente y evitamos división por cero
    progreso_porcentaje = int((caja_real / meta_total) * 100) if meta_total > 0 else 0
    faltante = meta_total - caja_real if meta_total > caja_real else 0

    # ==========================================
    # 2. DATOS PARA EL FORMULARIO (Los Selects)
    # ==========================================
    
    # Traemos solo a los aprendices activos, ordenados alfabéticamente
    aprendices = Usuario.objects.filter(rol='APRENDIZ', is_active=True).order_by('first_name')
    
    # Traemos solo los conceptos de pago que estén marcados como activos
    conceptos = ConceptoFondo.objects.filter(activo=True).order_by('nombre')

    # ==========================================
    # 3. DATOS PARA LA TABLA INFERIOR
    # ==========================================
    
    # Traemos los últimos 15 movimientos registrados, cruzando datos con select_related para mayor velocidad
    ultimos_movimientos = Fondo.objects.select_related('aprendiz', 'concepto').all().order_by('-fecha_creacion', '-id')[:15]

    # ==========================================
    # 4. EMPAQUETADO DEL CONTEXTO
    # ==========================================
    
    contexto = {
        'caja_real': caja_real,
        'cartera': cartera,
        'meta_total': meta_total,
        'progreso_porcentaje': progreso_porcentaje,
        'faltante': faltante,
        'aprendices': aprendices,
        'conceptos': conceptos,
        'movimientos': ultimos_movimientos,
        'titulo': 'Gestión de Fondos',
    }
    
    return render(request, 'inicio_fondo.html', contexto)