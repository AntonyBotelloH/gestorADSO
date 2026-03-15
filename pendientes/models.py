from django.db import models
from usuarios.models import Usuario, Ficha  # Ajusta esta ruta según donde tengas estos modelos

class Pendiente(models.Model):
    """Modelo para gestionar las tareas administrativas del instructor."""
    
    CATEGORIAS = [
        ('Sofia', 'Sofía Plus'),
        ('Calificaciones', 'Calificaciones'),
        ('Reuniones', 'Reuniones / Actas'),
        ('Planeacion', 'Planeación Pedagógica'),
        ('Otro', 'Otro'),
    ]

    PRIORIDADES = [
        ('Alta', '🔴 Alta'),
        ('Media', '🟡 Media'),
        ('Baja', '🔵 Baja'),
    ]

    # Relaciones
    instructor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='mis_pendientes', limit_choices_to={'rol': 'Instructor'})
    
    # Ficha puede ser nula porque en el HTML pusiste la opción "General (Sin Ficha)"
    ficha_vinculada = models.ForeignKey(Ficha, on_delete=models.SET_NULL, null=True, blank=True, related_name='tareas_instructor')

    # Datos de la tarea
    descripcion = models.CharField(max_length=255)
    categoria = models.CharField(max_length=30, choices=CATEGORIAS, default='Sofia')
    prioridad = models.CharField(max_length=15, choices=PRIORIDADES, default='Media')
    fecha_limite = models.DateField(null=True, blank=True)
    
    # Control de estado
    completada = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['completada', 'fecha_limite', '-creado_en']

    def __str__(self):
        estado = "✅" if self.completada else "⏳"
        return f"{estado} {self.descripcion} - {self.instructor.first_name}"