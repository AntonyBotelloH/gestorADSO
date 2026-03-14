"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static

from core.views import inicio, configuraciones
from usuarios.views import set_ficha_activa


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', inicio, name='inicio'),
    path('configuraciones/', configuraciones, name='configuraciones'),
    path('asistencia/', include('asistencia.urls')),
    path('fondos/', include('fondos.urls')),
    path('proyectos/', include('proyectos.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('planeacion/', include('planeacion.urls')),
    path('set-ficha/', set_ficha_activa, name='set_ficha_activa'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
