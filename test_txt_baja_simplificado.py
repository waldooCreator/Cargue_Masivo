#!/usr/bin/env python
"""
Script para verificar el TXT de baja simplificado (solo FID_ANTERIOR y coordenadas GPS)
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

def verificar_txt_baja_simplificado():
    """Verifica el formato del TXT de baja simplificado"""
    print("=== VERIFICACIÓN TXT BAJA SIMPLIFICADO ===")
    
    # Buscar el archivo TXT de baja más reciente
    media_path = "c:/Users/wvelasco/OneDrive - Grupo EPM/Escritorio/Cargue_Masivo/media/generated"
    
    import glob
    archivos_baja = glob.glob(os.path.join(media_path, "*_baja.txt"))
    
    if not archivos_baja:
        print("❌ No se encontraron archivos TXT de baja")
        return
    
    # Tomar el más reciente
    archivo_mas_reciente = max(archivos_baja, key=os.path.getmtime)
    print(f"📄 Archivo TXT de baja más reciente: {os.path.basename(archivo_mas_reciente)}")
    
    # Leer y analizar el archivo
    try:
        with open(archivo_mas_reciente, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        if not lines:
            print("❌ El archivo está vacío")
            return
        
        # Analizar encabezados
        header = lines[0].strip()
        campos = header.split('|')
        
        print(f"\n📋 Encabezados encontrados: {len(campos)}")
        for i, campo in enumerate(campos, 1):
            print(f"   {i}. {campo}")
        
        # Verificar que solo tenga los campos esperados
        campos_esperados = ['FID_ANTERIOR', 'COOR_GPS_LAT', 'COOR_GPS_LON']
        
        if campos == campos_esperados:
            print(f"\n✅ PERFECTO: Los encabezados coinciden exactamente con lo esperado")
        else:
            print(f"\n⚠️ DIFERENCIA DETECTADA:")
            print(f"   Esperado: {campos_esperados}")
            print(f"   Actual:   {campos}")
        
        # Analizar datos
        print(f"\n📊 Registros de datos: {len(lines) - 1}")
        
        if len(lines) > 1:
            print(f"\n🔍 Muestra de los primeros 3 registros:")
            for i in range(1, min(4, len(lines))):
                datos = lines[i].strip().split('|')
                print(f"   Registro {i}: FID={datos[0] if len(datos) > 0 else 'N/A'}, "
                      f"LAT={datos[1] if len(datos) > 1 else 'N/A'}, "
                      f"LON={datos[2] if len(datos) > 2 else 'N/A'}")
        
        print(f"\n🎯 RESUMEN:")
        print(f"   - Campos: {len(campos)} (esperados: 3)")
        print(f"   - Registros: {len(lines) - 1}")
        print(f"   - Formato correcto: {'✅ SÍ' if campos == campos_esperados else '❌ NO'}")
        
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")

if __name__ == "__main__":
    verificar_txt_baja_simplificado()