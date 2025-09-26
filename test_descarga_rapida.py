import os
import django
import sys

sys.path.append(r'C:\Users\wvelasco\OneDrive - Grupo EPM\Escritorio\Cargue_Masivo')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura

# Buscar cualquier proceso completado
proceso = ProcesoEstructura.objects.filter(estado='COMPLETADO').first()

if proceso:
    print(f"✅ Proceso encontrado: {proceso.id}")
    print(f"URLs de prueba:")
    print(f"http://127.0.0.1:8000/proceso/{proceso.id}/descargar/txt_baja/")
    print(f"http://127.0.0.1:8000/proceso/{proceso.id}/descargar/xml_baja/")
    print(f"\n��� Abrir en el navegador para probar descarga!")
else:
    print("❌ No hay procesos completados")
