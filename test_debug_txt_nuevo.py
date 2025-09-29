#!/usr/bin/env python
"""
Test para debug del TXT nuevo - ver qué datos están llegando
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura
from estructuras.services import FileGenerator

def test_debug_txt_nuevo():
    """Probar generación de TXT nuevo con debug extendido"""
    
    # Buscar el proceso específico
    proceso_id = "464059c1-0db9-4649-b73b-a2496c5cf251"
    
    try:
        proceso = ProcesoEstructura.objects.get(id=proceso_id)
        print(f"🎯 Generando TXT nuevo para proceso: {proceso.id}")
        print(f"   Archivo Excel: {proceso.archivo_excel}")
        
        generator = FileGenerator(proceso)
        resultado = generator.generar_txt()
        
        if resultado['exito']:
            print(f"✅ TXT nuevo generado: {resultado['archivo_txt']}")
        else:
            print(f"❌ Error: {resultado['error']}")
            
    except ProcesoEstructura.DoesNotExist:
        print(f"❌ No se encontró el proceso {proceso_id}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    print("🔧 Iniciando test debug TXT nuevo...\n")
    test_debug_txt_nuevo()
    print("\n✨ Test completado")