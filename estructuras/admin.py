from django.contrib import admin
from .models import ProcesoEstructura

@admin.register(ProcesoEstructura)
class ProcesoEstructuraAdmin(admin.ModelAdmin):
    list_display = ['id', 'resumen_clasificacion', 'estado', 'progreso_porcentaje', 'created_at']
    list_filter = ['estado', 'clasificacion_confirmada', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'progreso_porcentaje', 'clasificacion_automatica']
    search_fields = ['id']
    
    def progreso_porcentaje(self, obj):
        return f"{obj.progreso_porcentaje}%"
    progreso_porcentaje.short_description = "Progreso"
    
    def resumen_clasificacion(self, obj):
        if obj.clasificacion_confirmada:
            tipos = []
            if obj.total_expansion > 0:
                tipos.append(f"Exp({obj.total_expansion})")
            if obj.total_reposicion_nuevo > 0:
                tipos.append(f"RepN({obj.total_reposicion_nuevo})")
            if obj.total_reposicion_bajo > 0:
                tipos.append(f"RepB({obj.total_reposicion_bajo})")
            if obj.total_desmantelado > 0:
                tipos.append(f"Desm({obj.total_desmantelado})")
            return " + ".join(tipos) if tipos else "Sin clasificar"
        else:
            return f"Sin clasificar ({obj.registros_totales} regs)"
    resumen_clasificacion.short_description = "Clasificación"
