#!/usr/bin/env python3
"""
Script de prueba definitivo para verificar que TXT NUEVO no contenga registros con FID_ANTERIOR
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura
from estructuras.services import FileGenerator
import tempfile
import shutil

def crear_datos_prueba():
    """Crear datos de prueba mezclados: algunos con FID, otros sin FID"""
    return [
        {
            'UC': 'NUEVO_UC_001',
            'Código FID_rep': '',  # SIN FID - debe ir a TXT NUEVO
            'Nombre': 'PROPIETARIO_NUEVO_1',
            'COORDENADA_X': '1000000',
            'COORDENADA_Y': '2000000',
            'Codigo Inventario': 'MAT_NUEVO_001',
            'Norma': 'RETIE',
            'Poblacion': 'MEDELLIN'
        },
        {
            'UC': 'REEMPLAZO_UC_002',
            'Código FID_rep': '38142268',  # CON FID - NO debe ir a TXT NUEVO
            'Nombre': 'PROPIETARIO_REEMPLAZO_2',
            'COORDENADA_X': '1000100',
            'COORDENADA_Y': '2000100',
            'Codigo Inventario': 'MAT_REEMPLAZO_002',
            'Norma': 'RETIE',
            'Poblacion': 'MEDELLIN'
        },
        {
            'UC': 'NUEVO_UC_003',
            'Código FID_rep': None,  # SIN FID - debe ir a TXT NUEVO
            'Nombre': 'PROPIETARIO_NUEVO_3',
            'COORDENADA_X': '1000200',
            'COORDENADA_Y': '2000200',
            'Codigo Inventario': 'MAT_NUEVO_003',
            'Norma': 'RETIE',
            'Poblacion': 'MEDELLIN'
        },
        {
            'UC': 'REEMPLAZO_UC_004',
            'Código FID_rep': '99999999',  # CON FID - NO debe ir a TXT NUEVO
            'Nombre': 'PROPIETARIO_REEMPLAZO_4',
            'COORDENADA_X': '1000300',
            'COORDENADA_Y': '2000300',
            'Codigo Inventario': 'MAT_REEMPLAZO_004',
            'Norma': 'RETIE',
            'Poblacion': 'MEDELLIN'
        },
        {
            'UC': 'NUEVO_UC_005',
            'Código FID_rep': '',  # SIN FID - debe ir a TXT NUEVO
            'Nombre': 'PROPIETARIO_NUEVO_5',
            'COORDENADA_X': '1000400',
            'COORDENADA_Y': '2000400',
            'Codigo Inventario': 'MAT_NUEVO_005',
            'Norma': 'RETIE',
            'Poblacion': 'MEDELLIN'
        }
    ]

def main():
    print("=== VERIFICACIÓN DEFINITIVA: TXT NUEVO SIN FID_ANTERIOR ===")
    
    # Crear proceso de prueba
    proceso = ProcesoEstructura.objects.create(
        registros_totales=5,
        circuito='TEST_FID_FILTER'
    )
    
    print(f"✅ Proceso creado con ID: {proceso.id}")
    
    # Datos de prueba
    datos_prueba = crear_datos_prueba()
    proceso.datos_excel = datos_prueba
    proceso.save()
    
    print(f"📊 Datos de prueba: {len(datos_prueba)} registros")
    registros_sin_fid = sum(1 for r in datos_prueba if not (r.get('Código FID_rep') and str(r.get('Código FID_rep')).strip()))
    registros_con_fid = len(datos_prueba) - registros_sin_fid
    print(f"   - {registros_sin_fid} registros SIN FID (deben ir a TXT NUEVO)")
    print(f"   - {registros_con_fid} registros CON FID (NO deben ir a TXT NUEVO)")
    
    # Configurar directorio de salida
    media_path = Path(__file__).parent / 'media' / 'generated'
    media_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Generar TXT NUEVO
        print("\n📋 Generando TXT NUEVO...")
        file_gen = FileGenerator(proceso)
        txt_filename = file_gen.generar_txt()
        
        print(f"✅ TXT NUEVO: {txt_filename}")
        
        # Verificar contenido del TXT NUEVO
        from django.conf import settings
        media_generated = os.path.join(settings.MEDIA_ROOT, 'generated')
        txt_path = os.path.join(media_generated, txt_filename)
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
                
            # Primera línea son encabezados
            encabezados = lines[0].strip().split('|')
            datos_lines = lines[1:]
            
            print(f"\n🔍 ANÁLISIS DEL TXT NUEVO:")
            print(f"📄 Registros en archivo: {len(datos_lines)} (esperados: {registros_sin_fid})")
            
            if len(datos_lines) == registros_sin_fid:
                print("  ✅ CORRECTO: Número de registros coincide con los esperados sin FID")
            else:
                print(f"  ❌ ERROR: Se esperaban {registros_sin_fid} registros, pero se encontraron {len(datos_lines)}")
            
            # Verificar que NO hay campo FID_ANTERIOR en encabezados
            if 'FID_ANTERIOR' in encabezados:
                print("  ❌ ERROR: TXT NUEVO contiene campo FID_ANTERIOR en encabezados")
            else:
                print("  ✅ CORRECTO: TXT NUEVO no tiene campo FID_ANTERIOR en encabezados")
            
            # Verificar contenido de cada registro
            print(f"\n📋 VERIFICACIÓN DE CONTENIDO:")
            uc_encontradas = []
            for i, line in enumerate(datos_lines):
                campos = line.strip().split('|')
                # Buscar UC (debería estar en una posición específica)
                uc_pos = None
                for j, encabezado in enumerate(encabezados):
                    if encabezado == 'UC':
                        uc_pos = j
                        break
                
                if uc_pos is not None and uc_pos < len(campos):
                    uc = campos[uc_pos]
                    uc_encontradas.append(uc)
                    print(f"  Registro {i+1}: UC={uc}")
            
            # Verificar que solo están las UC esperadas (sin FID)
            uc_esperadas_sin_fid = ['NUEVO_UC_001', 'NUEVO_UC_003', 'NUEVO_UC_005']
            uc_no_deseadas = ['REEMPLAZO_UC_002', 'REEMPLAZO_UC_004']
            
            error_found = False
            for uc_no_deseada in uc_no_deseadas:
                if uc_no_deseada in uc_encontradas:
                    print(f"  ❌ ERROR CRÍTICO: {uc_no_deseada} encontrada en TXT NUEVO (tiene FID, no debería estar)")
                    error_found = True
            
            for uc_esperada in uc_esperadas_sin_fid:
                if uc_esperada not in uc_encontradas:
                    print(f"  ❌ ERROR: {uc_esperada} NO encontrada en TXT NUEVO (sin FID, debería estar)")
                    error_found = True
                else:
                    print(f"  ✅ CORRECTO: {uc_esperada} está en TXT NUEVO (sin FID)")
            
            if not error_found:
                print(f"\n🎉 PRUEBA EXITOSA: TXT NUEVO funciona PERFECTAMENTE")
                print("✅ Solo contiene registros sin FID_ANTERIOR")
                print("✅ No contiene ningún registro con FID_ANTERIOR")
                print("✅ Filtrado funcionando correctamente")
            else:
                print(f"\n💥 PRUEBA FALLIDA: Encontrados errores críticos")
                print("❌ TXT NUEVO contiene registros que NO debería tener")
        else:
            print(f"❌ ERROR: No se encontró el archivo {txt_path}")
    
    except Exception as e:
        print(f"❌ ERROR en prueba: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Limpiar archivos de prueba
        try:
            if 'txt_filename' in locals():
                from django.conf import settings
                media_generated = os.path.join(settings.MEDIA_ROOT, 'generated')
                txt_path = os.path.join(media_generated, txt_filename)
                if os.path.exists(txt_path):
                    os.unlink(txt_path)
                    print(f"\n🧹 Archivo de prueba eliminado: {txt_filename}")
        except Exception:
            pass
        
        # Eliminar proceso de prueba
        try:
            proceso.delete()
            print(f"🧹 Proceso de prueba eliminado: {proceso.id}")
        except Exception:
            pass

if __name__ == '__main__':
    main()