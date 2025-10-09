#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura
import pandas as pd

def debug_proceso_actual():
    print("🔧 Verificando qué archivo Excel está procesando el sistema actualmente...")
    
    # Obtener el último proceso activo
    procesos = ProcesoEstructura.objects.all().order_by('-id')[:5]
    
    for proceso in procesos:
        print(f"\n📋 Proceso ID: {proceso.id}")
        print(f"   Excel: {proceso.archivo_excel}")
        print(f"   Estado: {proceso.estado}")
        
        # Verificar si el archivo existe
        archivo_path = proceso.archivo_excel.path if hasattr(proceso.archivo_excel, 'path') else str(proceso.archivo_excel)
        if os.path.exists(archivo_path):
            print(f"   ✅ Archivo existe")
            
            # Leer y verificar contenido
            try:
                df = pd.read_excel(archivo_path)
                print(f"   📊 Filas: {len(df)}, Columnas: {len(df.columns)}")
                print(f"   📑 Columnas: {list(df.columns)}")
                
                # Buscar códigos operativos
                codigos_z_encontrados = False
                for columna in df.columns:
                    if df[columna].dtype == 'object':  # Solo columnas de texto
                        valores_z = df[columna].astype(str).str.contains(r'^Z\d+', na=False)
                        if valores_z.any():
                            codigos_z = df[columna][valores_z].tolist()
                            print(f"   🎯 Códigos Z en '{columna}': {codigos_z}")
                            codigos_z_encontrados = True
                
                if not codigos_z_encontrados:
                    print("   ❌ No se encontraron códigos operativos en este archivo")
                    
            except Exception as e:
                print(f"   ❌ Error leyendo archivo: {e}")
        else:
            print(f"   ❌ Archivo no existe: {archivo_path}")

if __name__ == "__main__":
    debug_proceso_actual()