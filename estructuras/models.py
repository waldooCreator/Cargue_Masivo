from django.db import models
import uuid

class ProcesoEstructura(models.Model):
    ESTADOS = [
        ('INICIADO', 'Iniciado'),
        ('CLASIFICANDO', 'Clasificando Automáticamente'),
        ('CLASIFICADO', 'Clasificado para Revisión'),
        ('PROCESANDO', 'Procesando'),
        ('COMPLETANDO_DATOS', 'Completando Datos'),
        ('GENERANDO_ARCHIVOS', 'Generando Archivos'),
        ('COMPLETADO', 'Completado'),
        ('ERROR', 'Error')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    archivo_excel = models.FileField(upload_to='uploads/excel/')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='INICIADO')
    circuito = models.CharField(max_length=100, blank=True)
    
    # Resultados de clasificación automática
    clasificacion_automatica = models.JSONField(default=dict, blank=True)  # Resultado del clasificador
    clasificacion_confirmada = models.BooleanField(default=False)  # Si el usuario confirmó la clasificación
    ajustes_clasificacion = models.JSONField(default=list, blank=True)  # Ajustes manuales del usuario
    
    # Resumen de estructuras por tipo (después de clasificación)
    total_expansion = models.IntegerField(default=0)
    total_reposicion_nuevo = models.IntegerField(default=0) 
    total_reposicion_bajo = models.IntegerField(default=0)
    total_desmantelado = models.IntegerField(default=0)
    
    # Campos de control (solo para mostrar progreso)
    registros_totales = models.IntegerField(default=0)
    registros_procesados = models.IntegerField(default=0)
    errores = models.JSONField(default=list, blank=True)
    
    # Datos procesados (almacenados temporalmente para completar campos)
    datos_excel = models.JSONField(default=list, blank=True)
    datos_norma = models.JSONField(default=list, blank=True)
    campos_faltantes = models.JSONField(default=dict, blank=True)
    archivos_generados = models.JSONField(default=dict, blank=True)  # {'txt': 'filename.txt', 'xml': 'filename.xml'}
    estadisticas_clasificacion = models.JSONField(default=dict, blank=True)  # Estadísticas de aplicación de reglas
    
    # Control de propietarios
    propietario_definido = models.CharField(max_length=50, blank=True)  # Propietario asignado por el usuario
    requiere_definir_propietario = models.BooleanField(default=False)  # Si necesita definir propietario
    
    # Control de estado de salud
    estado_salud_definido = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        choices=[
            ('BUENO', 'Bueno'),
            ('REGULAR', 'Regular'),
            ('MALO', 'Malo'),
        ],
        help_text="Estado de salud definido por el usuario para todas las estructuras"
    )
    
    # Control de estado de estructura
    estado_estructura_definido = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('CONSTRUCCION', 'Construcción'),
            ('RETIRADO', 'Retirado'),
            ('OPERACION', 'Operación'),
        ],
        help_text="Estado de estructura definido por el usuario para todas las estructuras"
    )
    
    # Timestamps automáticos de Django
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Proceso de Estructura"
        verbose_name_plural = "Procesos de Estructuras"
        ordering = ['-created_at']
    
    def __str__(self):
        if self.clasificacion_confirmada:
            tipos_detectados = []
            if self.total_expansion > 0:
                tipos_detectados.append(f"Expansión({self.total_expansion})")
            if self.total_reposicion_nuevo > 0:
                tipos_detectados.append(f"Rep.Nuevo({self.total_reposicion_nuevo})")
            if self.total_reposicion_bajo > 0:
                tipos_detectados.append(f"Rep.Bajo({self.total_reposicion_bajo})")
            if self.total_desmantelado > 0:
                tipos_detectados.append(f"Desmantelado({self.total_desmantelado})")
            
            tipos_str = " + ".join(tipos_detectados) if tipos_detectados else "Sin clasificar"
            return f"Proceso {tipos_str} - {self.estado}"
        else:
            return f"Proceso {self.estado} - {self.registros_totales} registros"
    
    @property
    def progreso_porcentaje(self):
        if self.registros_totales > 0:
            return round((self.registros_procesados / self.registros_totales) * 100, 2)
        return 0
