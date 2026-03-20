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

# Fases fijas del proceso pedagógico SENA
FASE_CHOICES = [
    ('Análisis', 'Análisis'),
    ('Planeación', 'Planeación'),
    ('Ejecución', 'Ejecución'),
    ('Evaluación', 'Evaluación'),
]

class ActividadPlaneacion(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('En Curso', 'En Curso'),
        ('Terminada', 'Terminada'),
    ]

    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='planeaciones')
    fase = models.CharField(max_length=20, choices=FASE_CHOICES, verbose_name='Fase')
    
    # CAMBIO CLAVE: ManyToManyField permite asociar varios RAPs a una sola actividad
    raps = models.ManyToManyField(ResultadoAprendizaje, related_name='actividades', verbose_name="Resultados de Aprendizaje")
    
    instructor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, limit_choices_to={'rol': 'INSTRUCTOR'})
    
    actividad_proyecto = models.TextField(verbose_name="Actividad de Proyecto")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='Pendiente')

    class Meta:
        verbose_name = "Actividad de Planeación"
        verbose_name_plural = "Actividades de Planeación"

    def __str__(self):
        return f"{self.ficha.codigo_ficha} - {self.fase} - {self.actividad_proyecto[:30]}"