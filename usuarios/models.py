from django.db import models
from django.contrib.auth.models import AbstractUser

class Ficha(models.Model):
    JORNADA_CHOICES = [
        ('Diurna', 'Diurna'),
        ('Nocturna', 'Nocturna'),
        ('Mixta', 'Mixta'),
    ]
    codigo_ficha = models.CharField(max_length=8, unique=True, verbose_name='Código de Ficha')
    programa = models.CharField(max_length=150, verbose_name='Programa de Formación')
    jornada = models.CharField(max_length=10, choices=JORNADA_CHOICES, verbose_name='Jornada')
    
    class Meta:
        verbose_name = 'Ficha'
        verbose_name_plural = 'Fichas'
        
    def __str__(self):
        return f"{self.codigo_ficha} - {self.programa}"

class Usuario(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('INSTRUCTOR', 'Instructor'),
        ('APRENDIZ', 'Aprendiz'),
    ]
    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('TI', 'Tarjeta de Identidad'),
        ('PP', 'Pasaporte'),
    ]
    
    first_name = models.CharField(max_length=150, blank=False, verbose_name='Nombres')
    last_name = models.CharField(max_length=150, blank=False, verbose_name='Apellidos')
    
    tipo_documento = models.CharField(max_length=2, choices=TIPO_DOCUMENTO_CHOICES, verbose_name='Tipo de Documento')
    documento = models.CharField(max_length=20, unique=True, verbose_name='Número de Documento')
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, default='APRENDIZ', verbose_name='Rol del Usuario')
    ficha = models.ForeignKey(Ficha, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Ficha')
    
    REQUIRED_FIELDS = ['documento', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class GrupoProyecto(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre del Equipo de Scrum')
    integrantes = models.ManyToManyField(Usuario, related_name='grupos_proyecto', verbose_name='Integrantes del Grupo de Proyecto')
    
    class Meta:
        verbose_name = 'Grupo de Proyecto'
        verbose_name_plural = 'Grupos de Proyecto'
        
    def __str__(self):
        return self.nombre