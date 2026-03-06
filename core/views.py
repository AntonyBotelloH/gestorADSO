from django.shortcuts import render


def inicio(request):
    
    context = {
        'titulo': 'Inicio',
    }
    return render(request, 'index.html', context)



    return render(request, 'core/inicio.html')