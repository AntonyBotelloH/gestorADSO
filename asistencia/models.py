from django.db import models
from usuarios.models import Ficha, Usuario

class SesionClase(models.Model):
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='sesiones_clase')
    fecha = models.DateField(auto_now_add=True, verbose_name="Fecha de Sesión")
    tema_tratado = models.CharField(max_length=200, blank=True, null=True, verbose_name="Tema o Actividad")
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Sesión de Clase"
        verbose_name_plural = "Sesiones de Clase"
        ordering = ['-fecha']

    def __str__(self):
        return f"Sesión {self.ficha.codigo_ficha} - {self.fecha}"

class RegistroAsistencia(models.Model):
    ESTADO_CHOICES = [
        ('Presente', '✅ Presente'),
        ('Retardo', '⏳ Retardo'),
        ('Falla', '❌ Falla Injustificada'),
        ('Excusa', '📄 Falla Justificada (Excusa)'),
    ]

    sesion = models.ForeignKey(SesionClase, on_delete=models.CASCADE, related_name='registros')
    aprendiz = models.ForeignKey(Usuario, on_delete=models.CASCADE, limit_choices_to={'rol': 'APRENDIZ'})
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Presente')
    comentario = models.CharField(max_length=200, blank=True, null=True, help_text="Ej: Llegó 20 min tarde por trancón")

    class Meta:
        verbose_name = "Registro de Asistencia"
        verbose_name_plural = "Registros de Asistencia"
        unique_together = ('sesion', 'aprendiz') # Un aprendiz no puede tener dos registros el mismo día

    def __str__(self):
        return f"{self.aprendiz.first_name} - {self.estado}"