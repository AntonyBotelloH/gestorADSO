from django.db import models
from django.conf import settings
from usuarios.models import Ficha, Usuario

class Proyecto(models.Model):
    ESTADOS_PROYECTO = [
        ('Al Día', '🟢 Al Día'),
        ('Observaciones', '🟡 Con Observaciones'),
        ('Atrasado', '🔴 Atrasado'),
    ]

    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='proyectos')
    nombre = models.CharField(max_length=200)
    objetivo = models.TextField(blank=True, null=True)
    scrum_master = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='proyectos_liderados')
    integrantes = models.ManyToManyField(Usuario, related_name='proyectos_asignados')
    estado = models.CharField(max_length=20, choices=ESTADOS_PROYECTO, default='Al Día')
    fecha_inicio = models.DateField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - Ficha {self.ficha.codigo_ficha}"

# --- ¡NUEVO MODELO SPRINT! ---
class Sprint(models.Model):
    ESTADOS_SPRINT = [
        ('Planificado', '📅 Planificado'),
        ('Activo', '▶️ Activo'),
        ('Completado', '✅ Completado'),
    ]
    
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='sprints')
    scrum_master = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='sprints_liderados')
    nombre = models.CharField(max_length=50, help_text="Ej: Sprint 1, Sprint 2...")
    objetivo = models.TextField(blank=True, help_text="Objetivo del Sprint (Sprint Goal)")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS_SPRINT, default='Planificado')
    
    def __str__(self):
        return f"{self.nombre} ({self.proyecto.nombre})"

class Tarea(models.Model):
    ESTADOS_TAREA = [
        ('To Do', 'Por Hacer'),
        ('In Progress', 'En Proceso'),
        ('Done', 'Terminado'),
    ]
    PRIORIDADES = [
        ('Alta', '🔴 Alta'),
        ('Media', '🟡 Media'),
        ('Baja', '🔵 Baja'),
    ]

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='tareas')
    # NUEVO: Conexión al Sprint. Si está nulo, la tarea vive en el "Product Backlog"
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='tareas_sprint')
    
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    responsable = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_TAREA, default='To Do')
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default='Media')
    fecha_limite = models.DateField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nombre

class DailyScrum(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='dailies')
    # NUEVO: Conectamos el Daily al Sprint Activo
    sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE, related_name='dailies_sprint', null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    # Las 3 preguntas de Scrum
    logros = models.TextField(verbose_name="¿Qué hicieron ayer?")
    planes = models.TextField(verbose_name="¿Qué harán hoy?")
    bloqueos = models.TextField(verbose_name="¿Tienen bloqueos?", blank=True)
    
    # Reporte de novedades internas
    aprendiz_reportado = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='reportes_daily')
    motivo_reporte = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Daily {self.fecha.date()} - {self.proyecto.nombre}"

class RevisionTecnica(models.Model):
    RESULTADOS = [
        ('Aprobado', '🟢 Aprobado'),
        ('Observaciones', '🟡 Con Observaciones'),
        ('Atrasado', '🔴 Atrasado'),
    ]

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='revisiones')
    # NUEVO: Reemplazamos el texto libre de 'hito' por la validación real de un Sprint cerrado
    sprint_evaluado = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='evaluaciones')
    instructor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField()
    estado_resultado = models.CharField(max_length=20, choices=RESULTADOS, default='Aprobado')
    aplicado = models.BooleanField(default=False)
    def __str__(self):
        sprint_nombre = self.sprint_evaluado.nombre if self.sprint_evaluado else "General"
        return f"Revisión {sprint_nombre} - {self.proyecto.nombre}"