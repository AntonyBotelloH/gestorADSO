from django.db import models
from usuarios.models import Ficha, Usuario  # Asegúrate de que la ruta coincida con tu app de usuarios

class EstrategiaPedagogica(models.Model):
    """Catálogo de estrategias o actividades para planes de mejora."""
    nombre = models.CharField(max_length=200, help_text="Ej. Taller de nivelación")
    descripcion = models.TextField(help_text="Detalle de la actividad a realizar")
    plazo_dias = models.PositiveIntegerField(default=5, help_text="Días estándar para cumplirla")
    activa = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.plazo_dias} días)"

class LlamadoAtencion(models.Model):
    """Registro principal de una novedad disciplinaria o académica."""
    
    INSTANCIAS = [
        ('Verbal', '🟡 Llamado Verbal'),
        ('Escrito', '🔴 Llamado Escrito'),
        ('Comite', '⚫ Comité de Evaluación'),
    ]
    
    CATEGORIAS = [
        ('Academica', 'Académica (Técnica)'),
        ('Disciplinaria', 'Disciplinaria (Comportamental)'),
    ]

    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='llamados')
    # Limitamos para que solo se pueda sancionar a los aprendices
    aprendiz = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='llamados_recibidos', limit_choices_to={'rol': 'Aprendiz'})
    instructor_reporta = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='llamados_reportados')
    
    instancia = models.CharField(max_length=20, choices=INSTANCIAS, default='Verbal')
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='Academica')
    fecha_incidente = models.DateField()
    descripcion_hechos = models.TextField()
    
    creado_en = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_instancia_display()} - {self.aprendiz.get_full_name()}"

class PlanMejoramiento(models.Model):
    """Asignación de una estrategia a un llamado de atención específico."""
    
    ESTADOS = [
        ('Pendiente', '⏳ Pendiente'),
        ('Cumplido', '✅ Cumplido'),
        ('Incumplido', '❌ Incumplido'),
    ]

    # Un llamado de atención tiene un único plan de mejora asociado
    llamado = models.OneToOneField(LlamadoAtencion, on_delete=models.CASCADE, related_name='plan_mejora')
    estrategia = models.ForeignKey(EstrategiaPedagogica, on_delete=models.RESTRICT)
    
    fecha_limite = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente')
    observaciones_cierre = models.TextField(blank=True, null=True, help_text="Comentarios al evaluar si cumplió o no.")

    def __str__(self):
        return f"Plan: {self.estrategia.nombre} -> {self.llamado.aprendiz.first_name}"