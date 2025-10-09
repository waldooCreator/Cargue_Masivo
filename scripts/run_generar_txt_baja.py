import os
import sys
import traceback

# Ajustar al directorio del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')

import django
django.setup()

from estructuras.models import ProcesoEstructura
from estructuras.services import FileGenerator


def main():
    try:
        # Intentar obtener el último proceso creado
        proceso = ProcesoEstructura.objects.order_by('-created_at').first()
        if not proceso:
            print('No se encontró ningún ProcesoEstructura en la base de datos')
            return

        print('Proceso seleccionado:', proceso.id)
        print('Estado del proceso:', proceso.estado)

        datos_excel = proceso.datos_excel or []
        datos_norma = proceso.datos_norma or []

        print(f'datos_excel: {len(datos_excel)} registros')
        if len(datos_excel) > 0:
            print('Ejemplo datos_excel[0]:', datos_excel[0])
        print(f'datos_norma: {len(datos_norma)} registros')
        if len(datos_norma) > 0:
            print('Ejemplo datos_norma[0]:', datos_norma[0])

        fg = FileGenerator(proceso)
        print('Llamando a generar_txt_baja() ...')
        filename = fg.generar_txt_baja()
        print('generar_txt_baja devolvió:', filename)

        filepath = os.path.join(fg.base_path, filename)
        print('Archivo esperado en:', filepath)
        print('Existe archivo?:', os.path.exists(filepath))

    except Exception as e:
        print('ERROR durante ejecución:')
        traceback.print_exc()


if __name__ == '__main__':
    main()
