from django.urls import path
from asistencia.views import inicio_asistencia, historial_asistencias, estadisticas_asistencia, justificar_falla, cerrar_sesion, detalle_sesion, registro_sofia, probar_conexion_sofia, probar_rol_sofia, probar_navegacion_sofia, probar_seleccion_ficha_sofia, probar_seleccion_aprendiz_sofia, probar_consulta_inasistencia_sofia, sincronizar_falla_sofia, detalle_registro, consultar_inasistencias_sofia, purgar_imagenes_prueba

urlpatterns = [
    # Toma de asistencia diaria (o edición de una sesión específica)
    path('', inicio_asistencia, name='inicio_asistencia'),
    
    # Tabla de días anteriores y filtros por fecha
    path('historial/', historial_asistencias, name='historial_asistencia'),
    
    # Dashboard de rendimiento, retardos y riesgo de deserción
    path('estadisticas/', estadisticas_asistencia, name='estadisticas_asistencia'),
    
    # Justificar Falla desde el informe del usuario
    path('justificar/<int:registro_id>/', justificar_falla, name='justificar_falla'),
    
    # Cerrar sesión (bloquear edición futura)
    path('cerrar_sesion/<int:sesion_id>/', cerrar_sesion, name='cerrar_sesion'),
    
    # Detalle de inasistencias y retardos de una sesión específica
    path('detalle_sesion/<int:sesion_id>/', detalle_sesion, name='detalle_sesion'),
    
    # Detalle de un registro individual (para ver su captura de SOFIA)
    path('registro/<int:registro_id>/', detalle_registro, name='detalle_registro'),

    # Automatización SOFIA
    path('registro-sofia/', registro_sofia, name='registro_sofia'),
    path('registro-sofia/probar-conexion/', probar_conexion_sofia, name='probar_conexion_sofia'),
    path('registro-sofia/probar-rol/', probar_rol_sofia, name='probar_rol_sofia'),
    path('registro-sofia/probar-navegacion/', probar_navegacion_sofia, name='probar_navegacion_sofia'),
    path('registro-sofia/probar-seleccion/', probar_seleccion_ficha_sofia, name='probar_seleccion_ficha_sofia'),
    path('registro-sofia/probar-seleccion-aprendiz/', probar_seleccion_aprendiz_sofia, name='probar_seleccion_aprendiz_sofia'),
    path('registro-sofia/probar-consulta/', probar_consulta_inasistencia_sofia, name='probar_consulta_inasistencia_sofia'),
    path('registro-sofia/purgar/', purgar_imagenes_prueba, name='purgar_imagenes_prueba'),
    
    # Sincronización directa desde Detalle de Sesión
    path('detalle_sesion/sincronizar/<int:registro_id>/', sincronizar_falla_sofia, name='sincronizar_falla_sofia'),

    # Consulta directa de inasistencias por aprendiz
    path('registro-sofia/consultar-aprendiz/<int:usuario_id>/', consultar_inasistencias_sofia, name='consultar_inasistencias_sofia'),
]