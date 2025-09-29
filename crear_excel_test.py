#!/usr/bin/env python
"""
Crear archivo Excel de prueba con códigos operativos para probar el enriquecimiento Oracle
"""
import os
import django
import pandas as pd

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

def crear_excel_con_codigos_operativos():
    """Crear Excel de prueba con códigos operativos"""
    
    # Datos de prueba con códigos operativos conocidos
    datos = [
        {
            'COORDENADA_X': 'Z238163',  # Código operativo en coordenada X
            'COORDENADA_Y': '8.257043',
            'UBICACION': 'PRUEBA ORACLE 1',
            'GRUPO': 'ESTRUCTURAS EYT',
            'TIPO': 'PRIMARIO',
            'CLASE': 'POSTE',
            'UC': '',
            'NIVEL_TENSION': 3,
            'NORMA': 'NC-RA1-631',
            'TIPO_ADECUACION': 'RETENCION',
            'CLASIFICACION_MERCADO': 'RURAL',
            'PROYECTO': 'TEST001',
            'ENLACE': 'TEST1'
        },
        {
            'COORDENADA_X': '-73.240000',
            'COORDENADA_Y': 'Z238164',  # Código operativo en coordenada Y
            'UBICACION': 'PRUEBA ORACLE 2',
            'GRUPO': 'ESTRUCTURAS EYT',
            'TIPO': 'PRIMARIO',
            'CLASE': 'POSTE',
            'UC': '',
            'NIVEL_TENSION': 3,
            'NORMA': 'NC-RA1-631',
            'TIPO_ADECUACION': 'SUSPENSION',
            'CLASIFICACION_MERCADO': 'RURAL',
            'PROYECTO': 'TEST002',
            'ENLACE': 'TEST2'
        },
        {
            'COORDENADA_X': '-73.250000',
            'COORDENADA_Y': '8.270000',
            'UBICACION': 'PRUEBA NORMAL',
            'GRUPO': 'ESTRUCTURAS EYT',
            'TIPO': 'PRIMARIO',
            'CLASE': 'POSTE',
            'UC': '',
            'NIVEL_TENSION': 3,
            'NORMA': 'NC-RA1-631',
            'TIPO_ADECUACION': 'RETENCION',
            'CLASIFICACION_MERCADO': 'RURAL',
            'PROYECTO': 'TEST003',
            'ENLACE': 'TEST3'
        }
    ]
    
    # Crear DataFrame
    df = pd.DataFrame(datos)
    
    # Guardar Excel
    output_path = os.path.join('media', 'uploads', 'excel', 'test_codigos_operativos.xlsx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_excel(output_path, index=False)
    
    print(f"✅ Excel de prueba creado: {output_path}")
    print("📊 Contenido:")
    print(df.to_string(index=False))
    
    return output_path

if __name__ == "__main__":
    print("🔧 Creando Excel de prueba con códigos operativos...\n")
    archivo = crear_excel_con_codigos_operativos()
    print(f"\n✨ Archivo creado: {archivo}")
    print("\n🎯 Usa este archivo para probar el enriquecimiento Oracle")