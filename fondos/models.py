from django.db import models

from django.db import models
from django.utils import timezone

class ConceptoFondo(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre del Concepto')
    descripcion = models.TextField(blank=True, null=True, help_text='Explicación detallada de para qué es este fondo')
    activo = models.BooleanField(default=True, help_text='Desmarcar si este concepto ya no se usa')

    class Meta:
        verbose_name = 'Concepto de Fondo'
        verbose_name_plural = 'Conceptos de Fondos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Fondo(models.Model):
    ESTADO_PAGO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('MORA', 'En Mora'),
    ]

    aprendiz = models.ForeignKey(
        'usuarios.Usuario', 
        on_delete=models.CASCADE, 
        related_name='aportes_fondo',
        limit_choices_to={'rol': 'APRENDIZ'},
        verbose_name='Aprendiz'
    )
    
    concepto = models.ForeignKey(
        ConceptoFondo, 
        on_delete=models.PROTECT, # Protege la integridad referencial
        verbose_name='Concepto del Aporte',
        limit_choices_to={'activo': True} # Solo muestra los conceptos activos
    )
    
    descripcion = models.TextField(blank=True, null=True, help_text='Detalles adicionales del pago del aprendiz')
    valor = models.PositiveIntegerField(verbose_name='Valor (COP)', help_text='Monto en pesos colombianos')
    estado_pago = models.CharField(max_length=20, choices=ESTADO_PAGO_CHOICES, default='PENDIENTE', verbose_name='Estado del Pago')
    
    fecha_creacion = models.DateField(default=timezone.now, verbose_name='Fecha de Registro')
    fecha_limite = models.DateField(null=True, blank=True, verbose_name='Fecha Límite de Pago')
    fecha_pago = models.DateField(null=True, blank=True, verbose_name='Fecha en que realizó el pago')
    
    comprobante = models.FileField(
        upload_to='comprobantes_fondos/', 
        null=True, 
        blank=True, 
        help_text='Soporte de pago, recibo o transferencia (PDF/Imagen)'
    )

    class Meta:
        verbose_name = 'Registro de Fondo'
        verbose_name_plural = 'Registros de Fondos'
        ordering = ['-fecha_creacion', 'estado_pago']

    def __str__(self):
        return f"{self.concepto.nombre} - {self.aprendiz} (${self.valor})"