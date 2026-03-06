
from django.shortcuts import render


# Create your views here.
from django.shortcuts import render
from .models import Usuario

def inicio_usuario(request):
    # 1. Consultamos a todos los usuarios registrados en la base de datos, 
    # ordenados alfabéticamente por nombre. 
    # (Más adelante le agregaremos el filtro para que solo traiga los de una ficha específica).
    lista_usuarios = Usuario.objects.all().order_by('first_name')

    # 2. Armamos el diccionario de contexto uniendo tus variables 
    # con el motor de breadcrumbs.
    context = {
        'nombre': 'Antony', # Tu variable original
        'titulo': 'Aprendices y Roles', # Alimenta el <h3> principal
        
        # La lista mágica que automatiza la navegación:
        'breadcrumbs': [
            {'nombre': 'Ficha', 'url': '#'}, # Aquí luego pondremos la URL de resumen de ficha
            {'nombre': 'Directorio', 'url': ''} # La vista actual (Directorio) no lleva enlace
        ],
        
        # Enviamos los datos reales a la tabla
        'usuarios_ficha': lista_usuarios,
    }
    
    return render(request, 'inicio_usuarios.html', context)