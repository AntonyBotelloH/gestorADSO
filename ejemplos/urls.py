from django.urls import path
from . import views

urlpatterns = [
    # 1. READ: Ruta principal que muestra la tabla
    # URL: /ejemplos/productos/
    path('productos/', views.listar_productos, name='listar_productos'),

    # 2. CREATE: Ruta para el formulario de crear
    # URL: /ejemplos/productos/crear/
    path('productos/crear/', views.crear_producto, name='crear_producto'),

    # 3. UPDATE: Ruta para editar. 
    # ¡OJO! Usamos <int:id_producto> para capturar el número que viene en la URL 
    # y pasárselo como parámetro a la función en views.py
    # URL: /ejemplos/productos/editar/5/
    path('productos/editar/<int:id_producto>/', views.editar_producto, name='editar_producto'),

    # 4. DELETE: Ruta para el borrado lógico
    # URL: /ejemplos/productos/eliminar/5/
    path('productos/eliminar/<int:id_producto>/', views.eliminar_producto, name='eliminar_producto'),
]