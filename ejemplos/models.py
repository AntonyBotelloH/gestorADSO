from django.db import models

class Producto(models.Model):
    # CharField: Ideal para textos cortos. Obligatorio definir el max_length.
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Producto")
    
    # TextField: Ideal para textos largos. Puede quedar en blanco (blank=True, null=True).
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    
    # DecimalField: Perfecto para dinero. max_digits es el total de números, decimal_places los decimales.
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio ($)")
    
    # IntegerField: Números enteros, ideal para contar cuántos tenemos en bodega.
    stock = models.IntegerField(default=0, verbose_name="Cantidad en Inventario")
    
    # BooleanField: Falso o Verdadero. Excelente para el "Borrado Lógico" que les enseñaste.
    activo = models.BooleanField(default=True, verbose_name="¿Está disponible?")
    
    # DateTimeField: Guarda la fecha y hora automáticamente cuando se crea el registro.
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")

    class Meta:
        # Esto le dice a Django cómo llamar a la tabla en el panel de administración
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        # Ordena los productos alfabéticamente por defecto
        ordering = ['nombre']

    def __str__(self):
        # Así se mostrará el objeto en la consola o en el panel de administrador
        return f"{self.nombre} - ${self.precio} ({'Activo' if self.activo else 'Inactivo'})"