from django.db import models
from usuarios.models import Ficha, Usuario

class Concepto(models.Model):
    CATEGORIA_CHOICES = [
        ('Multa', 'Multa / Sanción'),
        ('Aporte', 'Aporte Voluntario'),
        ('Cuota', 'Cuota Fija (Ej. Salida)'),
        ('Gasto', 'Gasto (Egreso)'),
    ]
    
    TIPO_OPERACION_CHOICES = [
        ('Ingreso', '▲ Ingreso (Cobro)'),
        ('Egreso', '▼ Gasto (Egreso)'),
    ]
    
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Concepto")
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, verbose_name="Categoría")
    tipo_operacion = models.CharField(max_length=20, choices=TIPO_OPERACION_CHOICES, verbose_name="Tipo de Operación")
    valor_sugerido = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Valor Sugerido ($)")
    vigente_desde = models.DateField(verbose_name="Vigente Desde")
    activo = models.BooleanField(default=True, verbose_name="Estado (Activo/Inactivo)")

    class Meta:
        verbose_name = "Concepto de Fondo"
        verbose_name_plural = "Catálogo de Conceptos"
        ordering = ['-activo', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_operacion_display()})"


class MetaFinanciera(models.Model):
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='metas_financieras')
    nombre = models.CharField(max_length=150, verbose_name="Nombre de la Meta")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción / Justificación")
    valor_objetivo = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Valor Total Requerido ($)")
    fecha_limite = models.DateField(verbose_name="Fecha Límite de Recaudo")
    activa = models.BooleanField(default=True, verbose_name="Meta Activa")

    class Meta:
        verbose_name = "Meta Financiera"
        verbose_name_plural = "Metas Financieras"
        # Ordena para que las metas activas y con fecha más próxima salgan primero
        ordering = ['-activa', 'fecha_limite']

    def __str__(self):
        return f"{self.ficha.codigo_ficha} - {self.nombre} (${self.valor_objetivo})"

class Movimiento(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Ejecutado', 'Ejecutado'),
    ]
    
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='movimientos_fondos')
    responsable = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Aprendiz / Responsable")
    concepto = models.ForeignKey(Concepto, on_delete=models.PROTECT, verbose_name="Concepto")
    
    valor = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Valor ($)")
    
    # --- CAMBIOS AQUÍ ---
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_pago = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Pago Real")
    # --------------------
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Ejecutado', verbose_name="Estado")
    observacion = models.TextField(blank=True, null=True, verbose_name="Observación")

    class Meta:
        verbose_name = "Movimiento de Fondo"
        verbose_name_plural = "Historial de Movimientos"
        ordering = ['-fecha']

    def __str__(self):
        return f"Comprobante #{self.id:04d} - {self.concepto.nombre} - ${self.valor}"