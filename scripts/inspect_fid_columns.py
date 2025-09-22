import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')

import django
django.setup()

from estructuras.models import ProcesoEstructura

proceso = ProcesoEstructura.objects.order_by('-created_at').first()
if not proceso:
    print('No hay procesos en la DB')
    sys.exit(0)

print('Proceso:', proceso.id)
datos_excel = proceso.datos_excel or []
if not datos_excel:
    print('datos_excel vacío')
    sys.exit(0)

first = datos_excel[0]
print('Número de campos en el primer registro:', len(first))
print('Claves:')
for k in first.keys():
    print(' -', repr(k))

print('\nClaves que contienen "fid" o "ident":')
for k in first.keys():
    if isinstance(k, str) and ('fid' in k.lower() or 'ident' in k.lower()):
        print(' -', repr(k))

print('\nValores para claves que contienen fid/ident:')
for k in first.keys():
    if isinstance(k, str) and ('fid' in k.lower() or 'ident' in k.lower()):
        print(f"{k!r}: {first[k]!r}")
