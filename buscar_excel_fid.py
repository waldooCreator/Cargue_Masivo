#!/usr/bin/env python
"""
Buscar un proceso con Excel que contenga campo "Código FID_rep"
"""
import os
import django
import pandas as pd

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura

def buscar_excel_con_codigo_fid():
    """Buscar Excel que contenga campo Código FID_rep"""
    
    # Buscar procesos con Excel
    procesos = ProcesoEstructura.objects.filter(archivo_excel__isnull=False).order_by('-id')[:20]
    
    print(f"🔍 Examinando {len(procesos)} archivos Excel...")
    
    for proceso in procesos:
        try:
            excel_path = str(proceso.archivo_excel)
            # Construir ruta completa
            full_path = os.path.join('media', excel_path)
            
            if os.path.exists(full_path):
                print(f"\n📋 Proceso: {proceso.id}")
                print(f"   Archivo: {excel_path}")
                
                # Leer Excel y ver las columnas
                df = pd.read_excel(full_path)
                columnas = list(df.columns)
                
                # Buscar campo con "FID" o códigos operativos
                fid_fields = []
                codigo_fields = []
                
                for col in columnas:
                    col_lower = str(col).lower()
                    if 'fid' in col_lower and 'rep' in col_lower:
                        fid_fields.append(col)
                    elif any(keyword in col_lower for keyword in ['codigo', 'code', 'fid']):
                        codigo_fields.append(col)
                
                print(f"   Columnas FID_rep: {fid_fields}")
                print(f"   Columnas con código: {codigo_fields}")
                
                # Si encontramos campo FID_rep, mostrar algunos valores
                if fid_fields:
                    campo_fid = fid_fields[0]
                    valores_fid = df[campo_fid].head(5).tolist()
                    print(f"   📊 Valores en '{campo_fid}': {valores_fid}")
                    
                    # Verificar si hay códigos operativos (que empiecen con Z)
                    codigos_z = [v for v in valores_fid if str(v).strip().upper().startswith('Z')]
                    if codigos_z:
                        print(f"   ✅ ENCONTRADO! Códigos operativos: {codigos_z}")
                        return proceso.id, excel_path, campo_fid
                
                # También verificar otras columnas por códigos Z
                for col in columnas:
                    if df[col].dtype == 'object':  # Solo columnas de texto
                        valores_z = df[df[col].astype(str).str.upper().str.startswith('Z', na=False)][col].head(3).tolist()
                        if valores_z:
                            print(f"   🎯 Códigos Z en '{col}': {valores_z}")
                            return proceso.id, excel_path, col
                        
        except Exception as e:
            print(f"   ❌ Error leyendo {proceso.archivo_excel}: {e}")
    
    print("\n⚠️ No se encontró Excel con campo 'Código FID_rep' o códigos operativos")
    return None, None, None

if __name__ == "__main__":
    print("🔧 Buscando Excel con códigos operativos...\n")
    proceso_id, excel_path, campo = buscar_excel_con_codigo_fid()
    
    if proceso_id:
        print(f"\n✅ Excel encontrado!")
        print(f"   Proceso ID: {proceso_id}")
        print(f"   Archivo: {excel_path}")
        print(f"   Campo códigos: {campo}")
        print(f"\n🎯 Usa este proceso para probar el enriquecimiento Oracle")
    else:
        print(f"\n❌ No se encontró Excel adecuado")