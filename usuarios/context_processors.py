from .models import Ficha

def fichas_globales(request):
    # 1. Traemos todas las fichas para el selector
    fichas = Ficha.objects.all().order_by('codigo_ficha')
    
    ficha_activa = None
    # Como no cambiamos el nombre de la variable en la sesión, 
    # sigue llamándose 'ficha_activa_id', pero ahora guarda el CÓDIGO (ej. "2555555")
    codigo_seleccionado = request.session.get('ficha_activa_id')
    
    if codigo_seleccionado:
        try:
            # ¡CORRECCIÓN AQUÍ! Ahora busca por codigo_ficha
            ficha_activa = Ficha.objects.get(codigo_ficha=codigo_seleccionado)
        except Ficha.DoesNotExist:
            # Si no existe, limpiamos la basura de la sesión
            request.session['ficha_activa_id'] = None
    return {
        'lista_fichas': fichas,
        'ficha_activa': ficha_activa
    }