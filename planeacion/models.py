from django.db import models
from usuarios.models import Ficha, Usuario # Importamos para relacionar

class Competencia(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código de Competencia")
    nombre = models.TextField(verbose_name="Nombre de la Competencia")
    duracion_horas = models.PositiveIntegerField(verbose_name="Duración (Horas)")

    def __str__(self):
        return f"{self.codigo} - {self.nombre[:50]}..."

class ResultadoAprendizaje(models.Model):
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE, related_name='raps')
    descripcion = models.TextField(verbose_name="Descripción del RAP")

    def __str__(self):
        return f"RAP: {self.descripcion[:60]}..."

class FaseProyecto(models.Model):
    NOMBRE_CHOICES = [
        ('Análisis', 'Análisis'),
        ('Diseño', 'Diseño'),
        ('Desarrollo', 'Desarrollo'),
        ('Evaluación', 'Evaluación'),
    ]
    nombre = models.CharField(max_length=20, choices=NOMBRE_CHOICES, unique=True)
    orden = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['orden']
        verbose_name = "Fase de Proyecto"
        verbose_name_plural = "Fases de Proyecto"

    def __str__(self):
        return self.nombre

class ActividadPlaneacion(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('En Curso', 'En Curso'),
        ('Terminada', 'Terminada'),
    ]
    
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='planeaciones')
    fase = models.ForeignKey(FaseProyecto, on_delete=models.PROTECT)
    rap = models.ForeignKey(ResultadoAprendizaje, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, limit_choices_to={'rol': 'INSTRUCTOR'})
    
    actividad_proyecto = models.TextField(verbose_name="Actividad de Proyecto")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='Pendiente')

    class Meta:
        verbose_name = "Actividad de Planeación"
        verbose_name_plural = "Actividades de Planeación"

    def __str__(self):
        return f"{self.ficha.codigo_ficha} - {self.fase.nombre} - {self.actividad_proyecto[:30]}"
    
