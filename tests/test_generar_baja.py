import os
import pytest
from types import SimpleNamespace

# Inicializar Django para que las importaciones que usan settings y modelos funcionen
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
import django
django.setup()

from estructuras.services import FileGenerator

# Nota: Usamos SimpleNamespace como un stub ligero para ProcesoEstructura

MEDIA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'media'))
GENERATED_DIR = os.path.join(MEDIA_ROOT, 'generated')


class DummyProceso:
    def __init__(self, id, archivo_path, datos_excel=None, datos_norma=None, circuito='', propietario_definido=None):
        self.id = id
        # Construir atributo archivo_excel con .path
        self.archivo_excel = SimpleNamespace(path=archivo_path)
        self.datos_excel = datos_excel or []
        self.datos_norma = datos_norma or []
        self.circuito = circuito
        self.propietario_definido = propietario_definido
        self.estado = 'COMPLETADO'
        self.estado_salud_definido = None
        self.estado_estructura_definido = None
        self.clasificacion_confirmada = True

    def save(self):
        # stub para simular modelo
        pass


@pytest.fixture(autouse=True)
def ensure_generated_dir():
    # Asegurarse de que exista el directorio generated y esté limpio antes y después
    if os.path.exists(GENERATED_DIR):
        # Intentar eliminar archivos dentro del directorio, ignorar errores de permiso
        for root, dirs, files in os.walk(GENERATED_DIR):
            for name in files:
                try:
                    os.unlink(os.path.join(root, name))
                except Exception:
                    pass
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except Exception:
                    pass
    else:
        os.makedirs(GENERATED_DIR, exist_ok=True)
    yield
    # Cleanup
    if os.path.exists(GENERATED_DIR):
        for root, dirs, files in os.walk(GENERATED_DIR):
            for name in files:
                try:
                    os.unlink(os.path.join(root, name))
                except Exception:
                    pass
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except Exception:
                    pass


def test_generar_txt_baja_reprocesa_excel_y_crea_archivo():
    # Ruta al Excel de test que existe en el repo
    excel_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'media', 'uploads', 'excel'))
    # Buscar un archivo xlsx en ese folder
    archivos = [f for f in os.listdir(excel_path) if f.lower().endswith('.xlsx')]
    assert archivos, "No se encontró archivo Excel de test en media/uploads/excel"
    excel_file = os.path.join(excel_path, archivos[0])

    # Proporcionar datos_excel no vacío (registro vacío) para que la función no falle al iniciar el filtrado
    proceso = DummyProceso(id='test123', archivo_path=excel_file, datos_excel=[{}], datos_norma=[])

    fg = FileGenerator(proceso)
    # Determinar cuántos registros con FID detecta el reprocesado del Excel
    from estructuras.services import ExcelProcessor
    processor = ExcelProcessor(proceso)
    raw_datos, campos_faltantes = processor.procesar_archivo()

    expected_raw_filtrados = []
    for registro in raw_datos:
        if isinstance(registro, dict):
            for k, v in registro.items():
                try:
                    if isinstance(k, str) and 'fid' in k.lower():
                        if v not in (None, '') and str(v).strip().lower() not in ('', 'nan', 'none'):
                            expected_raw_filtrados.append(registro)
                            break
                except Exception:
                    continue

    # Si el Excel de ejemplo no tiene FID, la función debe lanzar excepción
    if len(expected_raw_filtrados) == 0:
        import pytest
        with pytest.raises(Exception):
            fg.generar_txt_baja()
        return

    # Si hay registros con FID en el Excel, generar y validar el archivo
    filename = fg.generar_txt_baja()
    assert filename.endswith('_baja.txt')
    filepath = os.path.join(fg.base_path, filename)
    assert os.path.exists(filepath)

    # Verificar que el archivo contenga más de una línea (header + registros)
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line for line in f.readlines() if line.strip()]
    assert len(lines) > 1

    # Comprobar que todas las filas exportadas corresponden a registros con FID
    registros = [line.strip().split('|') for line in lines[1:]]

    # Contar cuántos FID detecta el reprocesado del Excel (mismo algoritmo que usaría FileGenerator)
    from estructuras.services import ExcelProcessor
    processor = ExcelProcessor(proceso)
    raw_datos, campos_faltantes = processor.procesar_archivo()

    # Filtrar raw_datos por columnas que contengan 'fid' en su nombre
    expected_raw_filtrados = []
    for registro in raw_datos:
        if isinstance(registro, dict):
            found = False
            for k, v in registro.items():
                try:
                    if isinstance(k, str) and 'fid' in k.lower():
                        if v not in (None, '') and str(v).strip().lower() not in ('', 'nan', 'none'):
                            found = True
                            break
                except Exception:
                    continue
            if found:
                expected_raw_filtrados.append(registro)

    # El número de registros exportados (excluyendo header) debe ser igual al número detectado en el Excel
    assert len(registros) == len(expected_raw_filtrados)

    # Además, verificar que cada registro exportado contenga algún valor FID en alguna columna (incluyendo FID_ANTERIOR)
    fid_cols = [i for i, h in enumerate(header) if 'FID' in h.upper() or 'FID_ANTERIOR' in h.upper()]
    # Si no se incluyó FID_ANTERIOR en encabezados, considerar que puede aparecer como campo en los valores
    for row in registros:
        has_fid = False
        # Revisar columnas que parezcan FID
        for idx in fid_cols:
            if idx < len(row) and row[idx].strip() not in ('', 'nan'):
                has_fid = True
                break
        # Si no se detectó en columnas de encabezado, también buscar en todo el contenido de la fila
        if not has_fid:
            joined = '|'.join(row)
            if 'FID' in joined.upper():
                has_fid = True
        assert has_fid, f"Registro exportado sin FID detectado: {row}"


def test_generar_xml_baja_crea_archivo():
    excel_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'media', 'uploads', 'excel'))
    archivos = [f for f in os.listdir(excel_path) if f.lower().endswith('.xlsx')]
    assert archivos, "No se encontró archivo Excel de test en media/uploads/excel"
    excel_file = os.path.join(excel_path, archivos[0])

    proceso = DummyProceso(id='testxml', archivo_path=excel_file, datos_excel=[{}], datos_norma=[])

    fg = FileGenerator(proceso)
    filename = fg.generar_xml_baja()

    assert filename.endswith('_baja.xml')
    filepath = os.path.join(fg.base_path, filename)
    assert os.path.exists(filepath)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    assert '<Configuracion>' in content
    assert 'Campo0' in content or 'Campo' in content

