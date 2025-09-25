#!/usr/bin/env python
"""
Script para probar la generación completa de TXT de baja con el nuevo formato simplificado
"""
import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura
from estructuras.services import FileGenerator

def test_generar_baja_completo():
    print("🔄 Ejecutando generación completa de TXT de baja...")
    
    # Buscar un proceso con archivos generados
    procesos = ProcesoEstructura.objects.filter(
        archivo_excel__isnull=False, 
        datos_excel__isnull=False
    ).order_by('-created_at')
    
    if not procesos.exists():
        print("❌ No hay procesos con datos")
        return
    
    proceso = procesos.first()
    print(f"📄 Usando proceso: {proceso.id} (fecha: {proceso.created_at})")
    print(f"📁 Archivos actuales: {proceso.archivos_generados}")
    
    # Crear generador y generar TXT de baja
    try:
        generador = FileGenerator(proceso)
        resultado = generador.generar_txt_baja()
        print(f"✅ Resultado: {resultado}")
        
        # Buscar el archivo de baja generado
        proceso.refresh_from_db()
        print(f"📁 Archivos después: {proceso.archivos_generados}")
        
        # Verificar el contenido del archivo
        if proceso.archivos_generados:
            archivos = proceso.archivos_generados.split(',')
            archivo_baja = next((f for f in archivos if 'baja.txt' in f), None)
            
            if archivo_baja:
                archivo_path = BASE_DIR / "media" / "generated" / archivo_baja.strip()
                if archivo_path.exists():
                    print(f"\n📝 Verificando archivo: {archivo_path}")
                    with open(archivo_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    if lines:
                        header = lines[0].strip()
                        campos = header.split('\t')
                        print(f"🔍 Número de campos: {len(campos)}")
                        print(f"🔍 Campos encontrados: {campos}")
                        
                        if len(campos) == 3 and set(campos) == {'FID_ANTERIOR', 'COOR_GPS_LAT', 'COOR_GPS_LON'}:
                            print("✅ FORMATO CORRECTO: Solo FID_ANTERIOR y coordenadas GPS")
                        else:
                            print("❌ FORMATO INCORRECTO: Contiene campos adicionales")
                        
                        # Mostrar algunas líneas de datos
                        print("\n📊 Primeras 3 líneas de datos:")
                        for i, line in enumerate(lines[:4]):  # Header + 3 datos
                            print(f"  {i}: {line.strip()}")
                    else:
                        print("⚠️ Archivo vacío")
                else:
                    print(f"❌ Archivo no encontrado: {archivo_path}")
            else:
                print("❌ No se encontró archivo de baja en archivos generados")
        
    except Exception as e:
        print(f"❌ Error generando TXT de baja: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generar_baja_completo()