import os

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver


def renombrar_foto_perfil(instance, filename):
    # Extraemos la extensión original del archivo (ej. jpg, png)
    ext = filename.split('.')[-1]
    
    # Armamos el nuevo nombre usando el documento del usuario
    # Ejemplo: Si sube "foto_mia.jpg" y su cédula es 1049641572, quedará "1049641572.jpg"
    nuevo_nombre = f"{instance.documento}.{ext}"
    
    # Devolvemos la ruta completa donde debe guardarse
    return os.path.join('fotos_perfil', nuevo_nombre)
class Ficha(models.Model):
    JORNADA_CHOICES = [
        ('Diurna', 'Diurna'),
        ('Nocturna', 'Nocturna'),
        ('Mixta', 'Mixta'),
    ]
    
    # Agregamos las etapas del SENA
    ETAPA_CHOICES = [
        ('Lectiva', 'Etapa Lectiva'),
        ('Productiva', 'Etapa Productiva'),
        ('Terminada', 'Terminada / Certificada'),
    ]

    codigo_ficha = models.CharField(max_length=15, unique=True, verbose_name='Código de Ficha') # Le subí a 15 por si acaso los códigos crecen
    programa = models.CharField(max_length=150, verbose_name='Programa de Formación')
    jornada = models.CharField(max_length=10, choices=JORNADA_CHOICES, verbose_name='Jornada')
    
    # --- NUEVOS CAMPOS ---
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Fecha de Inicio')
    fecha_fin_lectiva = models.DateField(null=True, blank=True, verbose_name='Fin Etapa Lectiva')
    etapa = models.CharField(max_length=15, choices=ETAPA_CHOICES, default='Lectiva', verbose_name='Etapa Actual')
    is_active = models.BooleanField(default=True, verbose_name='Ficha Activa')
    
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
        ('VOCERO', 'Vocero'),
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
    
    # NUEVO CAMPO: Foto de perfil
    # upload_to indica la subcarpeta donde se guardarán (adentro de tu carpeta MEDIA)
    foto = models.ImageField(upload_to=renombrar_foto_perfil, null=True, blank=True, verbose_name='Foto de Perfil')
    
    # Nuevo campo: Fecha de nacimiento
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de Nacimiento')
    
    REQUIRED_FIELDS = ['documento', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    @property
    def edad(self):
        from datetime import date
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None
        # Si first_name tiene texto, lo convertimos a formato Título
        if self.first_name:
            self.first_name = self.first_name.title()
            
        # Hacemos lo mismo con last_name
        if self.last_name:
            self.last_name = self.last_name.title()
            
        # Continuamos con el proceso normal de guardado de Django
        super().save(*args, **kwargs)

class GrupoProyecto(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre del Equipo de Scrum')
    integrantes = models.ManyToManyField(Usuario, related_name='grupos_proyecto', verbose_name='Integrantes del Grupo de Proyecto')
    
    class Meta:
        verbose_name = 'Grupo de Proyecto'
        verbose_name_plural = 'Grupos de Proyecto'
        
    def __str__(self):
        return self.nombre

class UsuarioAuditoria(models.Model):
    usuario_editado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='auditorias', verbose_name='Usuario Editado')
    editor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='ediciones', verbose_name='Editor')
    ip_editor = models.CharField(max_length=45, null=True, blank=True, verbose_name='IP del Editor')  # IPv6 puede ser hasta 45 chars
    fecha_edicion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Edición')
    cambios = models.TextField(null=True, blank=True, verbose_name='Cambios Realizados')  # Opcional para describir cambios
    
    class Meta:
        verbose_name = 'Auditoría de Usuario'
        verbose_name_plural = 'Auditorías de Usuarios'
        ordering = ['-fecha_edicion']
        
    def __str__(self):
        return f"Edición de {self.usuario_editado} por {self.editor or 'Anónimo'} el {self.fecha_edicion.strftime('%Y-%m-%d %H:%M')}"
    
