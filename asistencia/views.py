from django.shortcuts import render

def inicio_asistencia(request):
    nombre= 'Antony'
    context = {
        'nombre': nombre,
        'titulo': 'Asistencia',
    }
    return render(request, 'inicio_asistencia.html', context)
