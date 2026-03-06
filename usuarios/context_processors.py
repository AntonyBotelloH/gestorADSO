from .models import Ficha

def fichas_globales(request):
    """
    Este procesador inyecta la lista de todas las fichas en TODAS las plantillas del proyecto.
    """
    # Traemos todas las fichas ordenadas por su código
    fichas = Ficha.objects.all().order_by('codigo_ficha')
    
    # Retornamos un diccionario. La llave 'lista_fichas' será la variable 
    # que podrás usar en tu HTML.
    return {'lista_fichas': fichas}