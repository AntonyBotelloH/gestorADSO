from django.shortcuts import render

# Create your views here.
def inicio_proyecto(request):
    nombre= 'Antony'
    context = {
        'nombre': nombre,
        'titulo': 'Proyectos',
    }
    return render(request, 'inicio_proyecto.html', context)
