import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')

import django
django.setup()

from estructuras.models import ProcesoEstructura
import pandas as pd

proceso = ProcesoEstructura.objects.order_by('-created_at').first()
if not proceso:
    print('No hay procesos en la DB')
    sys.exit(0)

archivo_path = proceso.archivo_excel.path
print('Proceso:', proceso.id)
print('Archivo Excel:', archivo_path)

# Leer todas las hojas
xls = pd.ExcelFile(archivo_path)
print('Hojas encontradas:', xls.sheet_names)

# Intentar leer la hoja seleccionada por el processor (esta lógica reproduce ExcelProcessor behavior simplificado)
sheet_name = None
if 'Estructuras_N1-N2-N3' in xls.sheet_names:
    sheet_name = 'Estructuras_N1-N2-N3'
else:
    sheet_name = xls.sheet_names[0]

print('Leyendo hoja:', sheet_name)
df = pd.read_excel(archivo_path, sheet_name=sheet_name, header=1)
print('Columnas (raw):')
for c in df.columns:
    print(' -', repr(c))

candidates = [c for c in df.columns if isinstance(c, str) and ('fid' in c.lower() or 'ident' in c.lower())]
print('\nColumnas candidatas con "fid" o "ident":')
print(candidates)

for c in candidates:
    non_null = df[c].dropna().unique()
    print(f"\nValores no nulos en columna {c!r} (total {len(non_null)}):")
    print(non_null[:20])

# Buscar en todo el dataframe si hay celdas con formato que parezcan FID (alfa-numéricos cortos)
print('\nBuscando valores que parezcan FID en todo el df (filas 0..10)')
for i, row in df.head(20).iterrows():
    row_vals = []
    for c in df.columns:
        v = row[c]
        if pd.notna(v):
            s = str(v).strip()
            if 1 <= len(s) <= 50 and any(ch.isalnum() for ch in s):
                if 'fid' in str(c).lower() or 'ident' in str(c).lower():
                    print(f'Fila {i} columna {c!r}: {s}')

print('\nListo')
