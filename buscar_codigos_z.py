#!/usr/bin/env python
"""
Buscar Excel que contenga códigos operativos Z específicos
"""
import os
import django
import pandas as pd
import glob

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

def buscar_excel_con_codigos_z():
    """Buscar Excel que contenga códigos Z específicos"""
    
    # Buscar todos los archivos Excel
    excel_files = glob.glob("media/uploads/excel/*.xlsx")
    
    print(f"🔍 Buscando en {len(excel_files)} archivos Excel...")
    
    codigos_buscados = ['Z238163', 'Z251390', 'Z144833']
    
    for excel_file in excel_files:
        try:
            print(f"\n📋 Analizando: {excel_file}")
            
            # Leer Excel con diferentes métodos para manejar encabezados
            try:
                # Intentar leer normalmente
                df = pd.read_excel(excel_file)
            except:
                # Si falla, intentar con header en fila 1
                df = pd.read_excel(excel_file, header=1)
            
            # Buscar códigos Z en cualquier columna
            encontrados = []
            for col in df.columns:
                if df[col].dtype == 'object':  # Solo columnas de texto
                    for codigo in codigos_buscados:
                        if df[col].astype(str).str.contains(codigo, na=False).any():
                            encontrados.append((col, codigo))
                            
                    # También buscar cualquier valor que empiece con Z
                    valores_z = df[df[col].astype(str).str.upper().str.startswith('Z', na=False)][col].unique()
                    if len(valores_z) > 0:
                        print(f"   🎯 Códigos Z encontrados en '{col}': {list(valores_z)[:5]}")
            
            if encontrados:
                print(f"   ✅ ARCHIVO CORRECTO ENCONTRADO!")
                print(f"   📂 Archivo: {excel_file}")
                for col, codigo in encontrados:
                    print(f"   📌 Código {codigo} en columna '{col}'")
                
                # Mostrar estructura del archivo
                print(f"\n📊 ESTRUCTURA DEL ARCHIVO:")
                print(f"   Filas: {len(df)}")
                print(f"   Columnas: {len(df.columns)}")
                print("   Nombres de columnas:")
                for i, col in enumerate(df.columns):
                    print(f"      {i+1:2d}. '{col}'")
                
                return excel_file
                
        except Exception as e:
            print(f"   ❌ Error leyendo {excel_file}: {e}")
    
    print("\n⚠️ No se encontró Excel con los códigos operativos específicos")
    return None

if __name__ == "__main__":
    print("🔧 Buscando Excel con códigos operativos Z238163, Z251390, Z144833...\n")
    archivo_encontrado = buscar_excel_con_codigos_z()
    
    if archivo_encontrado:
        print(f"\n✅ Excel con códigos operativos encontrado: {archivo_encontrado}")
        print("🎯 Este es el archivo que debe usar el sistema para el enriquecimiento Oracle")
    else:
        print("\n❌ No se encontró el Excel correcto")