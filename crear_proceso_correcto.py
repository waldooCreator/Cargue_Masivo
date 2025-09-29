#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura
from django.core.files import File
import shutil

def crear_proceso_con_excel_correcto():
    print("🔧 Creando nuevo proceso con el Excel que contiene códigos operativos...")
    
    # Archivo fuente correcto
    archivo_correcto = r"media/uploads/excel/test_codigos_operativos.xlsx"
    
    if not os.path.exists(archivo_correcto):
        print(f"❌ Error: No se encuentra el archivo {archivo_correcto}")
        return
    
    # Crear nuevo proceso
    proceso = ProcesoEstructura.objects.create(
        estado='INICIADO',
        circuito='TEST_CODIGOS_OPERATIVOS'
    )
    
    # Copiar el archivo correcto al proceso
    nombre_archivo = f"test_codigos_operativos_{proceso.id}.xlsx"
    destino = f"media/uploads/excel/{nombre_archivo}"
    
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    
    # Copiar archivo
    shutil.copy2(archivo_correcto, destino)
    
    # Asignar archivo al proceso
    with open(destino, 'rb') as f:
        proceso.archivo_excel.save(nombre_archivo, File(f), save=True)
    
    print(f"✅ Proceso creado: {proceso.id}")
    print(f"📂 Archivo asignado: {proceso.archivo_excel}")
    print(f"🎯 Este proceso tiene el Excel con códigos operativos Z238163")
    
    return proceso.id

if __name__ == "__main__":
    proceso_id = crear_proceso_con_excel_correcto()
    print(f"\n🚀 Usa este ID de proceso para pruebas: {proceso_id}")