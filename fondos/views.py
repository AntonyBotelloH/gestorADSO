from django.shortcuts import render

# Create your views here.
def inicio_fondo(request):
    nombre= 'Antony'
    context = {
        'nombre': nombre,
        'titulo': 'Fondo',
    }
    return render(request, 'inicio_fondo.html', context)
