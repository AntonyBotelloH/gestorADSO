from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def rol_requerido(*roles_permitidos):
    """
    Decorador que verifica si el usuario tiene uno de los roles permitidos.
    Si no los tiene, lo devuelve al inicio con un mensaje de error.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Asumiendo que tu modelo Usuario tiene un campo llamado 'rol'
            if request.user.is_authenticated and request.user.rol in roles_permitidos:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "Acceso denegado: Tu rol no tiene permisos para esta acción.")
                # Lo mandamos de vuelta a la página donde estaba, o al inicio
                return redirect(request.META.get('HTTP_REFERER', 'inicio'))
        return _wrapped_view
    return decorator