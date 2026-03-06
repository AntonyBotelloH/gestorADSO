
from django.shortcuts import render


# Create your views here.
def inicio_usuario(request):
    nombre= 'Antony'
    context = {
        'nombre': nombre,
        'titulo': 'Aprendices y Roles',
    }
    return render(request, 'inicio_usuarios.html', context)
