from django.db import models
from usuarios.models import Ficha, Usuario

# 1. Catálogo de estrategias (Lo que el instructor configura: "Taller", "Exposición")
class EstrategiaPedagogica(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre de la Estrategia")
    descripcion = models.TextField(verbose_name="Descripción de la actividad")
    plazo_dias = models.PositiveIntegerField(default=5, verbose_name="Plazo (Días)")

    class Meta:
        verbose_name = "Estrategia Pedagógica"
        verbose_name_plural = "Estrategias Pedagógicas"

    def __str__(self):
        return self.nombre

# 2. El registro del incidente (El llamado en sí)
class LlamadoAtencion(models.Model):
    TIPO_FALTA_CHOICES = [
        ('Academica', 'Falta Académica'),
        ('Disciplinaria', 'Falta Disciplinaria'),
    ]
    tipo_falta = models.CharField(max_length=15, choices=TIPO_FALTA_CHOICES, default='Academica')

    # 2. Calificación de la falta
    GRAVEDAD_CHOICES = [
        ('Leve', 'Leve'),
        ('Grave', 'Grave'),
        ('Gravisima', 'Gravísima'),
    ]
    gravedad = models.CharField(max_length=15, choices=GRAVEDAD_CHOICES, default='Leve')

    # 3. Actualizar las instancias para incluir las sanciones reales
    INSTANCIA_CHOICES = [
        ('Verbal', 'Llamado Verbal (Medida Formativa)'),
        ('Escrito', 'Llamado Escrito (Sanción)'),
        ('Comite', 'Remisión a Comité de Evaluación'),
        ('Condicionamiento', 'Condicionamiento de Matrícula'),
        ('Cancelacion', 'Cancelación de Matrícula'),
    ]
    instancia = models.CharField(max_length=20, choices=INSTANCIA_CHOICES, default='Verbal')
    
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='llamados')
    aprendiz = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='llamados_recibidos', 
        limit_choices_to={'rol': 'APRENDIZ'}
    )
    
    motivo_principal = models.CharField(max_length=200, verbose_name="Motivo Principal")
    descripcion = models.TextField(verbose_name="Descripción de los Hechos")
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    acta_adjunta = models.FileField(upload_to='actas_disciplinarias/', null=True, blank=True)

    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = "Llamado de Atención"
        verbose_name_plural = "Llamados de Atención"

    def __str__(self):
        fecha_str = self.fecha_registro.strftime('%d/%m/%Y') if self.fecha_registro else "Borrador"
        return f"{self.aprendiz.get_full_name()} - {self.get_instancia_display()} ({fecha_str})"

# 3. EL PLAN DE MEJORAMIENTO (El que faltaba)
class PlanMejoramiento(models.Model):
    ESTADO_CHOICES = [
        ('En Curso', 'En Curso / Pendiente'),
        ('Cumplido', 'Cumplido / Cerrado'),
        ('Incumplido', 'Incumplido / En Riesgo'),
    ]

    # Un plan nace a partir de un llamado/comité
    llamado = models.OneToOneField(LlamadoAtencion, on_delete=models.CASCADE, related_name='plan_mejoramiento', verbose_name="Llamado que lo origina")
    
    # Un plan puede tener una o varias estrategias (talleres, exposiciones)
    estrategias = models.ManyToManyField(EstrategiaPedagogica, verbose_name="Estrategias Asignadas")
    
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha Límite de Cumplimiento")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='En Curso')
    
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones Finales")

    class Meta:
        ordering = ['-fecha_fin']
        verbose_name = "Plan de Mejoramiento"
        verbose_name_plural = "Planes de Mejoramiento"

    def __str__(self):
        return f"Plan de {self.llamado.aprendiz.first_name} - {self.estado}"