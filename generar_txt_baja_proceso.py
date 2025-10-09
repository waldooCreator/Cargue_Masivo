#!/usr/bin/env python
"""
Script para generar archivo TXT baja para un proceso específico
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura
from estructuras.services import FileGenerator

def generar_txt_baja_proceso(proceso_id):
    """Genera archivo TXT baja para el proceso específico"""
    try:
        # Obtener el proceso
        proceso = ProcesoEstructura.objects.get(id=proceso_id)
        print(f"Proceso encontrado: {proceso_id}")
        print(f"Estado: {proceso.estado}")
        
        if not proceso.datos_norma:
            print("ERROR: El proceso no tiene datos_norma")
            return False
        
        print(f"Registros en datos_norma: {len(proceso.datos_norma)}")
        
        # Generar archivo TXT baja
        generator = FileGenerator(proceso)
        filename_generated = generator.generar_txt_baja()
        
        # El archivo se guarda en media/generated, copiarlo a media/outputs
        generated_filepath = os.path.join('media', 'generated', filename_generated)
        
        # Definir ruta del archivo en cache
        cache_filename = f"estructuras_{proceso_id}_baja.txt"
        filepath = os.path.join('media', 'outputs', cache_filename)
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Copiar archivo
        import shutil
        shutil.copy2(generated_filepath, filepath)
        
        print(f"Archivo generado: {filepath}")
        print(f"Tamaño: {os.path.getsize(filepath)} bytes")
        
        # Actualizar base de datos
        if not proceso.archivos_generados:
            proceso.archivos_generados = {}
        proceso.archivos_generados['txt_baja'] = cache_filename
        proceso.save()
        
        print("Base de datos actualizada correctamente")
        
        # Mostrar preview del contenido
        with open(filepath, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            print(f"\nPrimeras 5 líneas del archivo:")
            for i, linea in enumerate(lineas[:5]):
                print(f"{i+1}: {linea.strip()}")
        
        return True
        
    except ProcesoEstructura.DoesNotExist:
        print(f"ERROR: No se encontró el proceso con ID {proceso_id}")
        return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    proceso_id = "cc7d2aa9-8b37-4c8b-95e4-da3f23566678"
    print(f"Generando TXT baja para proceso: {proceso_id}")
    
    if generar_txt_baja_proceso(proceso_id):
        print("\n✅ TXT baja generado exitosamente")
    else:
        print("\n❌ Error al generar TXT baja")