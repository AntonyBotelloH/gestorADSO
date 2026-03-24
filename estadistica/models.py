from django.db import models
import os

# --- FUNCIÓN DE RUTAS DINÁMICAS ---
def ruta_archivo_sena(instance, filename):
    """
    Organiza los archivos físicamente usando la temática como carpeta 
    y el subtema como subcarpeta, conservando el nombre original del archivo.
    """
    # La temática será el nombre del modelo (ej: InformeMensual, LiquidacionMensual)
    tematica = instance.__class__.__name__
    
    # El subtema dependerá de si es un informe o un pago
    if hasattr(instance, 'mes_reporte') and hasattr(instance, 'contrato'):
        # Para Informes: Ej: "9219834_Marzo_2026"
        subtema = f"{instance.contrato.numero_contrato}_{instance.mes_reporte}"
    elif hasattr(instance, 'numero_pago') and hasattr(instance, 'contrato'):
        # Para Liquidaciones: Ej: "9219834_Pago_2"
        subtema = f"{instance.contrato.numero_contrato}_Pago_{instance.numero_pago}"
    else:
        subtema = "General"
        
    # Resultado final: /media/Tematica/Subtema/nombre_original.pdf
    return os.path.join(tematica, subtema, filename)


# --- MODELO CENTRAL ---
class Contrato(models.Model):
    numero_contrato = models.CharField(max_length=50, unique=True, verbose_name="Nº del Contrato")
    objeto_contractual = models.TextField(verbose_name="Objeto Contractual")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Total del Contrato")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
    # Útil para saber si ya gestionaste el formato de dependientes para este contrato
    tiene_dependientes_registrados = models.BooleanField(default=False)

    def __str__(self):
        return f"Contrato {self.numero_contrato}"


# --- MODELOS FINANCIEROS (PAGOS Y PLANILLAS) ---
class LiquidacionMensual(models.Model):
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='liquidaciones')
    periodo_inicio = models.DateField(verbose_name="Del")
    periodo_fin = models.DateField(verbose_name="Al")
    numero_pago = models.IntegerField(verbose_name="Número de pago")
    
    # Ingresos
    valor_bruto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Bruto Pago")
    base_retencion_fuente = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Base para Retención")
    
    # Seguridad Social (PILA)
    numero_planilla_pila = models.CharField(max_length=50, verbose_name="Nº Planilla PILA")
    ibc = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Ingreso Base de Cotización")
    aporte_salud = models.DecimalField(max_digits=10, decimal_places=2)
    aporte_pension = models.DecimalField(max_digits=10, decimal_places=2)
    aporte_arl = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Impuestos y Descuentos
    reteica = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Reteica")
    
    # Totales
    neto_a_pagar = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Neto a Pagar")

    # Archivo físico
    documento_soporte = models.FileField(
        upload_to=ruta_archivo_sena, 
        null=True, 
        blank=True,
        verbose_name="Formato de Liquidación PDF"
    )

    def __str__(self):
        return f"Pago {self.numero_pago} - {self.contrato.numero_contrato}"


# --- MODELOS TÉCNICOS (INFORMES DE EJECUCIÓN) ---
class Obligacion(models.Model):
    """Catálogo estático de las obligaciones de tu contrato."""
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='obligaciones')
    numeral = models.IntegerField(verbose_name="Nro. Obligación")
    descripcion = models.TextField(verbose_name="Texto de la Obligación")

    def __str__(self):
        return f"Obligación {self.numeral} - {self.contrato.numero_contrato}"

class InformeMensual(models.Model):
    """Cabecera del informe de ejecución."""
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='informes')
    mes_reporte = models.CharField(max_length=50, verbose_name="Mes del Informe (Ej: Marzo 2026)")
    fecha_presentacion = models.DateField(auto_now_add=True)
    
    # Relacionado al pago de PILA que se menciona al final del informe técnico
    numero_planilla_pila = models.CharField(max_length=50, verbose_name="Nro. Planilla PILA aportada")
    
    # Archivo físico
    archivo_informe = models.FileField(
        upload_to=ruta_archivo_sena, 
        null=True, 
        blank=True,
        verbose_name="PDF del Informe Firmado"
    )

    def __str__(self):
        return f"Informe {self.mes_reporte} - {self.contrato.numero_contrato}"

class EjecucionObligacion(models.Model):
    """El detalle de qué hiciste para cada obligación en un mes específico."""
    informe = models.ForeignKey(InformeMensual, on_delete=models.CASCADE, related_name='ejecuciones')
    obligacion = models.ForeignKey(Obligacion, on_delete=models.RESTRICT)
    acciones_realizadas = models.TextField(verbose_name="Acciones realizadas")
    
    # Campo para listar los nombres de los archivos entregados (viñetas)
    lista_evidencias_texto = models.TextField(
        verbose_name="Evidencias (Listado)", 
        help_text="Ej: - Obligación 1.pdf \n- Proyecto Formativo.pdf",
        blank=True
    )

    def __str__(self):
        return f"Ejecución Obl. {self.obligacion.numeral} - {self.informe.mes_reporte}"

class Desplazamiento(models.Model):
    """Registro de órdenes de viaje legalizadas anexas al informe."""
    informe = models.ForeignKey(InformeMensual, on_delete=models.CASCADE, related_name='desplazamientos')
    numero_orden_viaje = models.CharField(max_length=50, verbose_name="Nro. de la Orden de Viaje")
    lugar = models.CharField(max_length=200, verbose_name="Lugar de Desplazamiento")
    fecha_inicial = models.DateField(verbose_name="Fecha Inicial")
    fecha_final = models.DateField(verbose_name="Fecha Final")

    def __str__(self):
        return f"Viaje a {self.lugar} - Orden {self.numero_orden_viaje}"