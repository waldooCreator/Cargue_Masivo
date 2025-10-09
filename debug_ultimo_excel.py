#!/usr/bin/env python
"""
Debug específico para ver qué Excel se está procesando y qué campos tiene
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura
from estructuras.services import FileGenerator
import pandas as pd

def debug_ultimo_proceso():
    """Debug del último proceso creado"""
    
    # Buscar el proceso más reciente
    proceso = ProcesoEstructura.objects.filter(archivo_excel__isnull=False).order_by('-id').first()
    
    if proceso:
        print(f"🎯 PROCESO MÁS RECIENTE: {proceso.id}")
        print(f"   Archivo Excel: {proceso.archivo_excel}")
        print(f"   ID: {proceso.id}")
        
        # Leer el Excel original para ver qué campos tiene
        try:
            excel_path = str(proceso.archivo_excel)
            full_path = excel_path  # Usar ruta directa
            
            if os.path.exists(full_path):
                print(f"\n📋 LEYENDO EXCEL ORIGINAL: {full_path}")
                df = pd.read_excel(full_path)
                
                print(f"   📊 Filas: {len(df)}")
                print(f"   📊 Columnas: {len(df.columns)}")
                print(f"\n🔍 TODAS LAS COLUMNAS DEL EXCEL:")
                for i, col in enumerate(df.columns):
                    print(f"   {i+1:2d}. '{col}'")
                
                # Buscar campos específicos
                print(f"\n🎯 BÚSQUEDA DE CAMPOS CÓDIGOS:")
                campos_codigo = []
                for col in df.columns:
                    col_str = str(col).lower()
                    if any(keyword in col_str for keyword in ['fid', 'codigo', 'code']):
                        campos_codigo.append(col)
                        valores = df[col].head(3).tolist()
                        print(f"   ✓ '{col}': {valores}")
                
                if not campos_codigo:
                    print("   ❌ NO se encontraron campos con FID o código")
                
                # Verificar si hay códigos Z en cualquier columna
                print(f"\n🔍 BÚSQUEDA DE CÓDIGOS Z:")
                encontrado_z = False
                for col in df.columns:
                    if df[col].dtype == 'object':  # Solo texto
                        valores_z = df[df[col].astype(str).str.upper().str.startswith('Z', na=False)]
                        if not valores_z.empty:
                            encontrado_z = True
                            ejemplos = valores_z[col].head(3).tolist()
                            print(f"   🎯 CÓDIGOS Z en '{col}': {ejemplos}")
                
                if not encontrado_z:
                    print("   ❌ NO se encontraron códigos que empiecen con Z")
                
            else:
                print(f"   ❌ Archivo no existe: {full_path}")
        
        except Exception as e:
            print(f"   ❌ Error leyendo Excel: {e}")
    
    else:
        print("❌ No se encontró ningún proceso con Excel")

if __name__ == "__main__":
    print("🔧 Debug del último proceso subido...\n")
    debug_ultimo_proceso()
    print("\n✨ Debug completado")