#!/usr/bin/env python
"""
Listar archivos Excel disponibles
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura

def listar_archivos_excel():
    """Listar archivos Excel disponibles"""
    
    procesos = ProcesoEstructura.objects.filter(archivo_excel__isnull=False)[:15]
    
    print(f"📂 Archivos Excel disponibles ({len(procesos)} procesos):")
    for proceso in procesos:
        print(f"   {proceso.id}: {proceso.archivo_excel}")
        
        # Ver si tiene archivos generados
        if proceso.archivos_generados:
            archivos = ", ".join(proceso.archivos_generados.keys())
            print(f"      Archivos generados: {archivos}")
    
    print("\n🔍 Para probar TXT nuevo, usar un proceso que NO tenga 'txt' generado aún")

if __name__ == "__main__":
    listar_archivos_excel()