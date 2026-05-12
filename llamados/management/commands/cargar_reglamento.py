import csv
import os
from django.core.management.base import BaseCommand
from llamados.models import FaltaReglamento
from django.conf import settings

class Command(BaseCommand):
    help = 'Carga masivamente el catálogo de faltas del Acuerdo 009 desde un archivo CSV'

    def handle(self, *args, **kwargs):
        # 1. Asegurar la creación obligatoria del Artículo 29 (Llegadas tarde reiteradas)
        self.stdout.write(self.style.WARNING('Verificando Artículo 29...'))
        falta_art29, creada_art29 = FaltaReglamento.objects.get_or_create(
            capitulo="Artículo 29",
            defaults={
                'descripcion': "Llegadas tarde reiteradas a las sesiones de formación (Acumulación de 3 retardos).",
                'tipo_falta': 'Disciplinaria',
                'gravedad': 'Leve'
            }
        )
        if creada_art29:
            self.stdout.write(self.style.SUCCESS('✅ Se agregó automáticamente el Artículo 29 (Retardos) al manual.'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ El Artículo 29 ya estaba registrado en el manual.'))

        ruta_csv = os.path.join(settings.BASE_DIR, 'reglamento.csv')
        
        if not os.path.exists(ruta_csv):
            self.stdout.write(self.style.ERROR(f'❌ No se encontró el archivo en: {ruta_csv}'))
            return

        self.stdout.write(self.style.WARNING('Iniciando carga del manual...'))
        
        try:
            # 1. Usamos utf-8-sig para eliminar caracteres invisibles (BOM) que mete Excel
            with open(ruta_csv, mode='r', encoding='utf-8-sig') as archivo:
                
                # 2. Detectamos automáticamente si Excel usó comas o punto y coma
                primera_linea = archivo.readline()
                separador = ';' if ';' in primera_linea else ','
                archivo.seek(0) # Volvemos a poner el cursor al inicio del archivo
                
                lector = csv.DictReader(archivo, delimiter=separador)
                
                # Verificación de seguridad
                if 'capitulo' not in lector.fieldnames:
                    self.stdout.write(self.style.ERROR(f'❌ Los encabezados no coinciden. Se leyó: {lector.fieldnames}'))
                    return

                contador_creadas = 0
                contador_existentes = 0
                
                for fila in lector:
                    # get_or_create evita duplicados
                    falta, creada = FaltaReglamento.objects.get_or_create(
                        capitulo=fila['capitulo'].strip(),
                        descripcion=fila['descripcion'].strip(),
                        tipo_falta=fila['tipo_falta'].strip(),
                        gravedad=fila['gravedad'].strip()
                    )
                    
                    if creada:
                        contador_creadas += 1
                    else:
                        contador_existentes += 1
                        
            self.stdout.write(self.style.SUCCESS(f'✅ ¡Éxito! Se cargaron {contador_creadas} faltas nuevas.'))
            if contador_existentes > 0:
                self.stdout.write(self.style.WARNING(f'⚠️ {contador_existentes} faltas ya existían y fueron omitidas.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ocurrió un error al leer el CSV: {str(e)}'))