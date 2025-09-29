#!/usr/bin/env python
"""
Debug de Excel específico que sabemos que existe
"""
import os
import django
import pandas as pd

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

def debug_excel_especifico():
    """Debug de un Excel específico"""
    
    excel_path = "media/uploads/excel/aa.xlsx"
    
    if os.path.exists(excel_path):
        print(f"📋 LEYENDO EXCEL: {excel_path}")
        df = pd.read_excel(excel_path)
        
        print(f"   📊 Filas: {len(df)}")
        print(f"   📊 Columnas: {len(df.columns)}")
        print("\n🔍 TODAS LAS COLUMNAS DEL EXCEL:")
        for i, col in enumerate(df.columns):
            print(f"   {i+1:2d}. '{col}'")
        
        # Mostrar algunas filas
        print("\n📋 PRIMERAS 3 FILAS:")
        for i, row in df.head(3).iterrows():
            print(f"   Fila {i+1}:")
            for col in df.columns:
                valor = row[col]
                print(f"      {col}: {valor}")
            print("   ---")
        
        # Buscar códigos Z
        print("\n🔍 BÚSQUEDA DE CÓDIGOS Z:")
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
        print(f"❌ Archivo no existe: {excel_path}")

if __name__ == "__main__":
    print("🔧 Debug de Excel específico...\n")
    debug_excel_especifico()
    print("\n✨ Debug completado")