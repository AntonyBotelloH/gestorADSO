from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto

# ==========================================
# 1. READ: Leer y Listar productos activos
# ==========================================
def listar_productos(request):
    # Verificamos si el usuario quiere ver los inactivos a través de un parámetro en la URL
    mostrar_inactivos = request.GET.get('mostrar_inactivos') == 'true'

    if mostrar_inactivos:
        # Traemos TODOS los productos, sin filtrar por activos
        productos = Producto.objects.all()
    else:
        # El comportamiento por defecto: solo se muestran los productos activos
        productos = Producto.objects.filter(activo=True)
    
    contexto = {
        'lista_productos': productos,
        'mostrar_inactivos': mostrar_inactivos, # Pasamos el estado actual a la plantilla
    }
    
    return render(request, 'admin/index.html', contexto)


# ==========================================
# 2. CREATE: Crear un nuevo producto
# ==========================================
def crear_producto(request):
    # Si el usuario presiona el botón "Guardar" del formulario HTML (POST), procesamos los datos
    if request.method == 'POST':
        # Capturamos lo que el usuario escribió en los <input name="..."> del HTML
        v_nombre = request.POST.get('nombre')
        v_descripcion = request.POST.get('descripcion')
        v_precio = request.POST.get('precio')
        v_stock = request.POST.get('stock')
        
        
        # Usamos el ORM para CREAR el registro en la base de datos
        Producto.objects.create(
            nombre=v_nombre,
            descripcion=v_descripcion,
            precio=v_precio,
            stock=v_stock
        )
        
        # Después de guardar, lo redirigimos a la ruta de la lista para que vea su nuevo producto
        return redirect('listar_productos')
        
    # Si el usuario llega haciendo clic en un enlace (GET), le mostramos el formulario
    # (¡AQUÍ CAMBIAMOS LA RUTA A admin/crear.html!)
    return render(request, 'admin/crear.html')


# ==========================================
# 3. UPDATE: Editar un producto existente
# ==========================================
def editar_producto(request, id_producto):
    # Buscamos el producto específico por su ID. 
    producto_a_editar = get_object_or_404(Producto, id=id_producto)

    # Si es POST (Presionó "Actualizar"), sobreescribimos los datos
    if request.method == 'POST':
        producto_a_editar.nombre = request.POST.get('nombre')
        producto_a_editar.descripcion = request.POST.get('descripcion')
        producto_a_editar.precio = request.POST.get('precio')
        producto_a_editar.stock = request.POST.get('stock')
        
        producto_a_editar.activo = 'activo' in request.POST

        # ¡IMPORTANTE! Le decimos a la base de datos que guarde los cambios
        producto_a_editar.save()

        # Lo enviamos de vuelta a la lista principal
        return redirect('listar_productos')

    # Si es GET, le mostramos el formulario PRE-LLENADO con los datos actuales
    contexto = {
        'producto': producto_a_editar
    }
    # (¡AQUÍ CAMBIAMOS LA RUTA A admin/editar.html!)
    return render(request, 'admin/editar.html', contexto)


# ==========================================
# 4. DELETE: Eliminar un producto (Borrado Lógico)
# ==========================================
def eliminar_producto(request, id_producto):
    # Buscamos el registro por su ID
    producto_a_borrar = get_object_or_404(Producto, id=id_producto)
    
    # Borrado lógico: cambiamos su estado a inactivo
    producto_a_borrar.activo = False
    
    # Guardamos el cambio en la base de datos
    producto_a_borrar.save()
    
    # Redirigimos a la tabla principal
    return redirect('listar_productos')