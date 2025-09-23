#!/usr/bin/env python
"""
Script de prueba para verificar que el TXT Baja incluye correctamente los datos de Oracle
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura
from estructuras.services import FileGenerator
import pandas as pd

def test_txt_baja_con_oracle():
    """Prueba la generación de TXT Baja con integración Oracle"""
    print("=== PRUEBA DE TXT BAJA CON ORACLE ===")
    
    # 1. Crear datos de prueba que simulen un Excel con FID
    datos_prueba = [
        {
            'Código FID_rep': '38142268',  # FID de ejemplo que sabemos que existe
            'UC': 'TEST_UC_001',
            'Norma': 'RETIE',
            'Poblacion': 'TEST_CIUDAD',
            'COORDENADA_X': '1000000',
            'COORDENADA_Y': '2000000',
            'Codigo Inventario': 'MAT_001'
        },
        {
            'Código FID_rep': '99999999',  # FID que probablemente no existe
            'UC': 'TEST_UC_002', 
            'Norma': 'RETIE',
            'Poblacion': 'TEST_CIUDAD',
            'COORDENADA_X': '1000100',
            'COORDENADA_Y': '2000100',
            'Codigo Inventario': 'MAT_002'
        }
    ]
    
    try:
        # 2. Crear un proceso de prueba
        from django.core.files.base import ContentFile
        
        # Crear un archivo dummy para el test
        excel_content = ContentFile(b"dummy excel content", name="test_oracle.xlsx")
        
        proceso = ProcesoEstructura.objects.create(
            archivo_excel=excel_content,
            datos_excel=datos_prueba,
            estado='COMPLETADO',
            registros_totales=len(datos_prueba),
            registros_procesados=len(datos_prueba)
        )
        
        print(f"✅ Proceso creado con ID: {proceso.id}")
        
        # 3. Generar TXT Baja con Oracle
        print("📋 Generando TXT Baja con consultas Oracle...")
        generator = FileGenerator(proceso)
        filename = generator.generar_txt_baja()
        
        print(f"✅ TXT Baja generado: {filename}")
        
        # 4. Leer y analizar el archivo generado
        filepath = os.path.join('media/generated', filename)
        if os.path.exists(filepath):
            print(f"📄 Leyendo archivo: {filepath}")
            
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            print(f"📊 Archivo tiene {len(lines)} líneas")
            
            if len(lines) > 0:
                # Mostrar encabezados
                headers = lines[0].strip().split('|')
                print(f"🔍 Encabezados ({len(headers)}):")
                for i, header in enumerate(headers):
                    print(f"   {i+1}. {header}")
                
                # Verificar que están los nuevos campos Oracle
                if 'COOR_GPS_LAT' in headers and 'COOR_GPS_LON' in headers:
                    print("✅ Campos Oracle presentes en encabezados")
                    
                    lat_idx = headers.index('COOR_GPS_LAT')
                    lon_idx = headers.index('COOR_GPS_LON')
                    
                    # Mostrar datos de las primeras filas
                    for i, line in enumerate(lines[1:3]):  # Primeras 2 filas de datos
                        values = line.strip().split('|')
                        if len(values) > max(lat_idx, lon_idx):
                            lat_val = values[lat_idx]
                            lon_val = values[lon_idx]
                            print(f"📍 Fila {i+1}: LAT={lat_val}, LON={lon_val}")
                        else:
                            print(f"⚠️  Fila {i+1}: Datos incompletos")
                else:
                    print("❌ Campos Oracle NO encontrados en encabezados")
            else:
                print("❌ Archivo vacío")
        else:
            print(f"❌ Archivo no encontrado: {filepath}")
        
        # 5. Limpiar
        proceso.delete()
        if os.path.exists(filepath):
            os.remove(filepath)
            print("🧹 Archivos de prueba eliminados")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR en prueba: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_txt_baja_con_oracle()
    if success:
        print("\n🎉 PRUEBA EXITOSA: TXT Baja con Oracle funcionando correctamente")
    else:
        print("\n💥 PRUEBA FALLIDA: Revisar errores arriba")