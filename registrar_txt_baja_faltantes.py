#!/usr/bin/env python
"""
Script para registrar archivos TXT baja existentes que no están en la base de datos
"""
import os
import django
import glob

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura

def registrar_archivos_txt_baja_faltantes():
    """Encuentra y registra archivos TXT baja que existen pero no están registrados"""
    
    # Buscar todos los archivos TXT baja en media/generated
    pattern = os.path.join('media', 'generated', '*_baja.txt')
    archivos_encontrados = glob.glob(pattern)
    
    print(f"🔍 Encontrados {len(archivos_encontrados)} archivos TXT baja físicos")
    
    registrados = 0
    ya_registrados = 0
    errores = 0
    
    for archivo_path in archivos_encontrados:
        try:
            # Extraer el ID del proceso del nombre del archivo
            filename = os.path.basename(archivo_path)
            # formato: estructuras_UUID_baja.txt
            if filename.startswith('estructuras_') and filename.endswith('_baja.txt'):
                proceso_id = filename.replace('estructuras_', '').replace('_baja.txt', '')
                
                try:
                    # Buscar el proceso en la base de datos
                    proceso = ProcesoEstructura.objects.get(id=proceso_id)
                    
                    # Verificar si ya está registrado
                    if 'txt_baja' in proceso.archivos_generados:
                        ya_registrados += 1
                        print(f"✅ Ya registrado: {proceso_id}")
                    else:
                        # Registrar el archivo
                        proceso.archivos_generados['txt_baja'] = filename
                        proceso.save()
                        registrados += 1
                        print(f"🆕 Registrado: {proceso_id} -> {filename}")
                        
                except ProcesoEstructura.DoesNotExist:
                    print(f"⚠️ Proceso no encontrado en BD: {proceso_id}")
                    errores += 1
                    
        except Exception as e:
            print(f"❌ Error procesando {archivo_path}: {e}")
            errores += 1
    
    print(f"\n📊 Resumen:")
    print(f"   Registrados nuevos: {registrados}")
    print(f"   Ya registrados: {ya_registrados}")
    print(f"   Errores: {errores}")
    print(f"   Total archivos: {len(archivos_encontrados)}")

if __name__ == "__main__":
    print("🔧 Registrando archivos TXT baja faltantes...\n")
    registrar_archivos_txt_baja_faltantes()
    print("\n✨ Proceso completado")