#!/usr/bin/env python
"""
Script para probar la generación completa de TXT NUEVO con los encabezados actualizados
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

def test_generar_txt_nuevo():
    print("🔄 Ejecutando generación completa de TXT NUEVO...")
    
    # Buscar un proceso con datos
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
    
    # Crear generador y generar TXT NUEVO
    try:
        generador = FileGenerator(proceso)
        resultado = generador.generar_txt()
        print(f"✅ Resultado: {resultado}")
        
        # Verificar el contenido del archivo
        archivo_path = BASE_DIR / "media" / "generated" / resultado
        if archivo_path.exists():
            print(f"\n📝 Verificando archivo: {archivo_path}")
            with open(archivo_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if lines:
                header = lines[0].strip()
                campos = header.split('|')
                print(f"🔍 Número de campos: {len(campos)}")
                print(f"🔍 Encabezados encontrados:")
                for i, campo in enumerate(campos, 1):
                    print(f"  {i:2d}. {campo}")
                
                # Verificar que sean los encabezados esperados
                encabezados_esperados = [
                    'COORDENADA_X', 'COORDENADA_Y', 'GRUPO', 'TIPO', 'CLASE', 'USO', 'ESTADO', 
                    'TIPO_ADECUACION', 'PROPIETARIO', 'PORCENTAJE_PROPIEDAD', 'UBICACION',
                    'CODIGO_MATERIAL', 'FECHA_INSTALACION', 'FECHA_OPERACION', 'PROYECTO',
                    'EMPRESA', 'OBSERVACIONES', 'CLASIFICACION_MERCADO', 'TIPO_PROYECTO',
                    'ID_MERCADO', 'UC', 'ESTADO_SALUD', 'OT_MAXIMO', 'CODIGO_MARCACION',
                    'SALINIDAD', 'ENLACE'
                ]
                
                if campos == encabezados_esperados:
                    print("✅ ENCABEZADOS CORRECTOS: Coinciden exactamente con los solicitados")
                else:
                    print("❌ ENCABEZADOS INCORRECTOS")
                    print("Diferencias:")
                    for i, (actual, esperado) in enumerate(zip(campos, encabezados_esperados)):
                        if actual != esperado:
                            print(f"  Posición {i+1}: '{actual}' != '{esperado}'")
                
                # Mostrar algunas líneas de datos para verificar mapeo
                print("\n📊 Primeras 3 líneas de datos:")
                for i, line in enumerate(lines[:4]):  # Header + 3 datos
                    if i == 0:
                        print(f"  Header: {line.strip()}")
                    else:
                        valores = line.strip().split('|')
                        print(f"  Fila {i}: {len(valores)} valores")
                        # Mostrar algunos campos importantes para verificar mapeo
                        importantes = ['COORDENADA_X', 'COORDENADA_Y', 'PROYECTO', 'UC', 'PROPIETARIO']
                        for campo in importantes:
                            if campo in encabezados_esperados:
                                idx = encabezados_esperados.index(campo)
                                if idx < len(valores):
                                    print(f"    {campo}: '{valores[idx]}'")
            else:
                print("⚠️ Archivo vacío")
        else:
            print(f"❌ Archivo no encontrado: {archivo_path}")
        
    except Exception as e:
        print(f"❌ Error generando TXT NUEVO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generar_txt_nuevo()