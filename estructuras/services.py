import pandas as pd
from typing import List, Dict, Tuple
from datetime import datetime
import os
import re
from django.conf import settings
# XML utilities are imported where needed inside functions to keep module
# imports minimal and avoid unused import warnings.
from .constants import (
    ESTRUCTURAS_CAMPOS, MAPEO_EXCEL_A_SALIDA, REGLAS_CLASIFICACION, 
    CATALOGO_MATERIALES, MAPEO_UC_MATERIAL, ESTADOS_SALUD
)
from .models import ProcesoEstructura

class DataUtils:
    """Utilidades centralizadas para procesamiento de datos"""
    
    # Constantes centralizadas
    VALORES_DEFECTO = {
        'GRUPO': 'ESTRUCTURAS EYT',
        'TIPO': 'PRIMARIO',
        'CLASE': 'POSTE',
        'USO': 'DISTRIBUCION ENERGIA',
        'PORCENTAJE_PROPIEDAD': '100',
        'TIPO_PROYECTO': 'T2',
        'FECHA_DEFAULT': '01/01/2000',
        'ESTADO_DEFAULT': 'OPERACION',
        'ID_MERCADO': '161',
        'SALINIDAD': 'NO'
    }
    
    @staticmethod
    def formatear_fecha(fecha) -> str:
        """
        Formatea una fecha para mostrar solo la fecha sin la hora en formato DD/MM/YYYY
        """
        if not fecha or str(fecha).strip() == '':
            return ''
        
        try:
            fecha_str = str(fecha).strip()
            
            # Si ya está en formato DD/MM/YYYY, retornar tal como está
            import re
            if re.match(r'^\d{2}/\d{2}/\d{4}$', fecha_str):
                return fecha_str
            
            # Si es un objeto datetime de pandas
            if hasattr(fecha, 'strftime'):
                return fecha.strftime('%d/%m/%Y')
            
            # Si es una fecha de Excel (número serial)
            if isinstance(fecha, (int, float)):
                from datetime import datetime, timedelta
                # Fecha base de Excel: 1900-01-01
                fecha_base = datetime(1900, 1, 1)
                fecha_calculada = fecha_base + timedelta(days=fecha - 2)  # -2 por diferencia en Excel
                return fecha_calculada.strftime('%d/%m/%Y')
            
            # Si es string con formato diferente, intentar parsear
            if isinstance(fecha, str):
                # Remover hora si existe
                if ' ' in fecha_str:
                    fecha_str = fecha_str.split(' ')[0]
                
                # Intentar diferentes formatos
                formatos = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']
                for formato in formatos:
                    try:
                        fecha_obj = datetime.strptime(fecha_str, formato)
                        return fecha_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        continue
            
            # Si no se puede convertir, devolver string vacío
            return ''
            
        except Exception:
            return ''
    
    @staticmethod
    def limpiar_valor_para_txt(valor):
        """
        Limpia un valor para que no contenga caracteres problemáticos en el archivo TXT
        """
        if valor is None:
            return ''
        
        # Convertir a string
        valor_str = str(valor)
        
        # Reemplazar caracteres problemáticos
        valor_str = valor_str.replace('\n', ' ').replace('\r', ' ').replace('|', '-')
        
        # Limpiar espacios al inicio y final
        valor_str = valor_str.strip()
        
        # Limitar longitud máxima (algunos sistemas tienen límites)
        if len(valor_str) > 255:
            valor_str = valor_str[:252] + '...'
        
        return valor_str
    

class ExcelProcessor:
    """Procesa archivos Excel extrayendo y normalizando datos de estructura"""
    
    def __init__(self, proceso):
        self.proceso = proceso
        self.tipo_estructura = getattr(proceso, 'tipo_estructura', 'EXPANSION')
        self.estructura_config = ESTRUCTURAS_CAMPOS.get(self.tipo_estructura, {})
        self.clasificador = ClasificadorEstructuras()
    
    def procesar_archivo(self) -> Tuple[List[Dict], List[str]]:
        """
        Procesa el archivo Excel del proceso y retorna datos y campos faltantes
        
        Returns:
            Tuple[List[Dict], List[str]]: (datos_procesados, campos_faltantes)
        """
        try:
            archivo_path = self.proceso.archivo_excel.path
            print(f"Procesando archivo: {archivo_path}")
            
            # Leer todas las hojas del Excel
            df_dict = pd.read_excel(archivo_path, sheet_name=None)
            
            # Determinar qué hoja usar basado en el modo de clasificación
            if self.proceso.clasificacion_confirmada:
                # FORZAR USO DE LA HOJA ESTRUCTURAS PARA DEBUG
                nombre_hoja = None
                
                # Buscar específicamente la hoja de estructuras
                if 'Estructuras_N1-N2-N3' in df_dict:
                    nombre_hoja = 'Estructuras_N1-N2-N3'
                    print(f"FORZANDO uso de hoja de estructuras: '{nombre_hoja}'")
                else:
                    # Fallback al algoritmo original si no existe esa hoja
                    mejor_puntaje = 0
                    print(f"Buscando la hoja correcta entre {len(df_dict)} hojas disponibles...")
                    
                    # Buscar en todas las hojas la que tenga más columnas de normas
                    for hoja_nombre, df_temp in df_dict.items():
                        try:
                            columnas_hoja = [str(col).strip() for col in df_temp.columns]
                            print(f"Revisando hoja '{hoja_nombre}' con {len(columnas_hoja)} columnas")
                            
                            # Calcular puntaje basado en columnas clave encontradas
                            puntaje = 0
                            
                            for col in columnas_hoja:
                                col_lower = str(col).lower().strip()
                                # Buscar coincidencias más flexibles
                                if ('norma' in col_lower or 
                                    'poblacion' in col_lower or 'población' in col_lower or 'municipio' in col_lower or
                                    'unidad' in col_lower and 'constructiva' in col_lower or
                                    'codigo' in col_lower and 'inventario' in col_lower or
                                    'material' in col_lower or
                                    'altura' in col_lower):
                                    puntaje += 1
                                    print(f"    Columna clave encontrada: '{col}'")
                            
                            print(f"  Hoja '{hoja_nombre}': puntaje {puntaje}/6 columnas clave")
                            
                            if puntaje > mejor_puntaje:
                                mejor_puntaje = puntaje
                                nombre_hoja = hoja_nombre
                                print(f"  Nueva mejor hoja: '{nombre_hoja}' con puntaje {puntaje}")
                        
                        except Exception as e:
                            print(f"  Error revisando hoja '{hoja_nombre}': {e}")
                            continue
                    
                    # Si no encuentra hoja específica, usar la primera
                    if not nombre_hoja:
                        nombre_hoja = list(df_dict.keys())[0]
                        print(f"No se encontró hoja específica, usando la primera: '{nombre_hoja}'")
                        
                    print(f"Hoja seleccionada: '{nombre_hoja}' (puntaje: {mejor_puntaje}/6)")
            else:
                # Buscar hoja de datos específica
                hoja_datos = self.estructura_config['ARCHIVOS_FUENTE']['hoja_datos']
                if hoja_datos in df_dict:
                    nombre_hoja = hoja_datos
                else:
                    # Fallback: usar la primera hoja
                    nombre_hoja = list(df_dict.keys())[0]
                    print(f"Hoja '{hoja_datos}' no encontrada, usando '{nombre_hoja}'")
            
            # Leer la hoja sin headers para investigar
            datos_df_raw = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=None)
            print("Primeras 5 filas del Excel:")
            for i in range(min(5, len(datos_df_raw))):
                print(f"Fila {i}: {list(datos_df_raw.iloc[i].values)}")
            
            # Intentar diferentes estrategias para encontrar headers
            datos_df = None
            header_row = None
            
            # Estrategia 1: Headers en fila 0 (default)
            try:
                temp_df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=0)
                # Verificar si tiene headers válidos (no solo "Unnamed" y no todos nan)
                valid_headers = [col for col in temp_df.columns if not col.startswith('Unnamed:') and str(col) != 'nan']
                if len(valid_headers) > 3:  # Al menos 3 headers válidos
                    datos_df = temp_df
                    header_row = 0
                    print("Headers encontrados en fila 0")
            except Exception:
                pass
            
            # Estrategia 2: Headers en fila 1
            if datos_df is None:
                try:
                    temp_df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=1)
                    # Verificar si tiene headers válidos
                    valid_headers = [col for col in temp_df.columns if not col.startswith('Unnamed:') and str(col) != 'nan']
                    if len(valid_headers) > 3:  # Al menos 3 headers válidos
                        datos_df = temp_df
                        header_row = 1
                        print("Headers encontrados en fila 1")
                except Exception:
                    pass
            
            # Estrategia 3: Headers en fila 2
            if datos_df is None:
                try:
                    temp_df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=2)
                    if not all(col.startswith('Unnamed:') for col in temp_df.columns):
                        datos_df = temp_df
                        header_row = 2
                        print("Headers encontrados en fila 2")
                except Exception:
                    pass
            
            # Si no encontramos headers válidos, usar fila 0 como fallback
            if datos_df is None:
                datos_df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=0)
                header_row = 0
                print("Usando fila 0 como headers (fallback)")
            
            print(f"Datos de hoja '{nombre_hoja}': {len(datos_df)} filas (header en fila {header_row})")
            
            # Normalizar nombres de columnas
            datos_df.columns = [self._normalizar_columna(col) for col in datos_df.columns]
            print(f"Columnas encontradas: {list(datos_df.columns)}")
            
            # Verificar campos requeridos
            campos_faltantes = self._verificar_campos(datos_df.columns)
            
            if campos_faltantes:
                print(f"Campos faltantes: {campos_faltantes}")
                print(f"Se encontraron: {list(datos_df.columns)}")
                return [], campos_faltantes
            
            # Convertir a lista de diccionarios y limpiar NaN
            datos = []
            for _, row in datos_df.iterrows():
                registro = {}
                for col, val in row.items():
                    if pd.isna(val):
                        registro[col] = ""
                    else:
                        # Formatear fechas directamente al leer del Excel
                        if self._es_campo_fecha(col) and val:
                            # Si es un campo de fecha, formatear inmediatamente
                            registro[col] = self._formatear_fecha_excel(val)
                        else:
                            registro[col] = str(val).strip()
                datos.append(registro)
            
            print(f"Registros procesados: {len(datos)}")
            
            return datos, []
            
        except Exception as e:
            print(f"Error procesando Excel: {str(e)}")
            raise Exception(f"Error procesando Excel: {str(e)}")
    
    def _normalizar_columna(self, columna: str) -> str:
        """Normaliza nombres de columnas manteniendo errores tipográficos del Excel"""
        return str(columna).strip()
    
    def _verificar_campos(self, columnas_excel: List[str]) -> List[str]:
        """Verifica qué campos obligatorios faltan"""
        # Usar validación permisiva por defecto (mapeo de equivalencias)
        # Mapeo de equivalencias de nombres de campos (ACTUALIZADO con columnas reales del Excel)
        equivalencias = {
            'Norma': ['Norma', 'NORMA', 'norma'],
            'UC': ['UC', 'Unidad_Constructiva', 'Unidad Constructiva', 'UNIDAD_CONSTRUCTIVA', 
                   'unidad_constructiva', 'unidad constructiva', 'Unnamed: 25'],
            'Poblacion': ['Poblacion', 'POBLACION', 'poblacion', 'Población', 'MUNICIPIOS', 'Municipios', 'Municipio', 'municipio'],
            'CODIGO_MATERIAL': ['Codigo Inventario', 'CODIGO_INVENTARIO', 'Unnamed: 23', 'Material', 'MATERIAL']
        }
        
        # Solo verificar campos básicos
        campos_basicos = ['Norma', 'UC', 'Poblacion']
        campos_faltantes = []
        
        print(f"DEBUG: Verificando campos básicos: {campos_basicos}")
        print(f"DEBUG: Columnas del Excel: {columnas_excel}")
        
        for campo in campos_basicos:
            campo_encontrado = False
            posibles_nombres = equivalencias.get(campo, [campo])
            print(f"DEBUG: Buscando campo '{campo}' en posibles nombres: {posibles_nombres}")
            
            for col in columnas_excel:
                if str(col).strip() in posibles_nombres:
                    print(f"DEBUG: Campo '{campo}' encontrado como '{col}'")
                    campo_encontrado = True
                    break
            
            if not campo_encontrado:
                print(f"DEBUG: Campo '{campo}' NO encontrado")
                campos_faltantes.append(campo)
        
        return campos_faltantes
    
    def _es_campo_fecha(self, nombre_columna: str) -> bool:
        """Verifica si una columna es un campo de fecha"""
        nombre_lower = nombre_columna.lower()
        return 'fecha' in nombre_lower or 'instalacion' in nombre_lower
    
    def _formatear_fecha_excel(self, fecha) -> str:
        """
        Formatea fechas leídas directamente del Excel a formato DD/MM/YYYY
        """
        return DataUtils.formatear_fecha(fecha)

class DataTransformer:
    """Transformador de datos del Excel de entrada a estructura de salida"""
    
    def __init__(self, tipo_estructura: str):
        self.tipo_estructura = tipo_estructura
        self.mapeo = MAPEO_EXCEL_A_SALIDA.get(tipo_estructura, {})
        self.estructura_config = ESTRUCTURAS_CAMPOS[tipo_estructura]
        self.clasificador = ClasificadorEstructuras()
    
    def _normalizar_nombres_campos(self, registro: Dict) -> Dict:
        """Normaliza los nombres de campos para que coincidan con el mapeo esperado"""
        equivalencias = {
            'Unidad_Constructiva': 'UC',
            'Unidad Constructiva': 'UC',
            'Unnamed: 25': 'UC',  # Para archivos con encabezados genéricos
            'Unnamed: 23': 'CODIGO_INVENTARIO',  # Para código de inventario
            'Unnamed: 0': 'COORDENADA_X',  # Para coordenada X
            'Unnamed: 1': 'COORDENADA_Y',  # Para coordenada Y
            'UNIDAD_CONSTRUCTIVA': 'UC',
            'unidad_constructiva': 'UC',
            'unidad constructiva': 'UC',
            'Código FID_rep': 'Código FID_rep',
            'FID_ANTERIOR': 'FID_ANTERIOR',
            'Tipo_accion_sal': 'Tipo_accion_sal',
            'Tipo_accion_ent': 'Tipo_accion_ent'
        }
        
        registro_normalizado = {}
        for campo, valor in registro.items():
            # Usar el nombre normalizado si existe, sino usar el original
            campo_normalizado = equivalencias.get(campo, campo)
            registro_normalizado[campo_normalizado] = valor
        
        return registro_normalizado
    
    def transformar_datos(self, datos_excel: List[Dict]) -> List[Dict]:
        """Transforma datos del Excel a la estructura de salida"""
        datos_transformados = []
        
        for registro_excel in datos_excel:
            # Normalizar nombres de campos en el registro
            registro_normalizado = self._normalizar_nombres_campos(registro_excel)
            registro_salida = {}
            
            # Mapear campos según el tipo de estructura
            for campo_excel, campo_salida in self.mapeo.items():
                valor = registro_normalizado.get(campo_excel, "")
                
                # Formatear fechas durante el mapeo
                if campo_salida in ['FECHA_INSTALACION', 'FECHA_OPERACION'] and valor:
                    valor = self.clasificador._formatear_fecha(str(valor))
                
                registro_salida[campo_salida] = valor
            
            # Agregar campos faltantes con valores por defecto
            for campo_salida in self.estructura_config['CAMPOS_SALIDA_DATOS']:
                if campo_salida not in registro_salida:
                    registro_salida[campo_salida] = ""
            
            # APLICAR REGLAS DE CLASIFICACIÓN
            registro_salida = self.clasificador.clasificar_estructura(registro_salida)
            
            # REGLA ESPECIAL: EMPRESA debe tener el mismo valor que PROPIETARIO para todos los tipos
            propietario = registro_salida.get('PROPIETARIO', '')
            registro_salida['EMPRESA'] = propietario
            
            datos_transformados.append(registro_salida)
        
        return datos_transformados
    
    def obtener_estadisticas_clasificacion(self, datos_transformados: List[Dict]) -> Dict:
        """Obtiene estadísticas de la clasificación aplicada"""
        return self.clasificador.obtener_resumen_clasificacion(datos_transformados)

class DataMapper:
    """Mapeador de datos Excel a estructura de norma"""
    
    def __init__(self, tipo_estructura: str):
        self.tipo_estructura = tipo_estructura
        self.estructura_config = ESTRUCTURAS_CAMPOS[tipo_estructura]
    
    def mapear_a_norma(self, datos_excel: List[Dict], circuito: str = "") -> List[Dict]:
        """Mapea datos del Excel al formato de norma"""
        
        datos_norma = []
        
        for registro in datos_excel:
            norma_registro = {
                'ENLACE': registro.get('ENLACE', ''),  # Campo Identificador mapeado a ENLACE
                'NORMA': registro.get('NORMA', ''),  # Campo Norma del Excel
                'CIRCUITO': circuito,
                'CODIGO_TRAFO': registro.get('CODIGO_TRAFO', ''),  # Opcional
                'CANTIDAD': self._calcular_cantidad(registro),
                'FECHA_INSTALACION': registro.get('FECHA_INSTALACION', ''),
                'TIPO_ADECUACION': registro.get('TIPO_ADECUACION', ''),  # "retencion o suspensión"
                'OBSERVACIONES': registro.get('OBSERVACIONES', ''),  # Campo observaciones
                'UC': registro.get('UC', ''),  # IMPORTANTE: Preservar UC para clasificación
                'ESTADO_SALUD': registro.get('ESTADO_SALUD', ''),  # IMPORTANTE: Preservar estado de salud
                'NIVEL_TENSION': registro.get('NIVEL_TENSION', ''),  # IMPORTANTE: Preservar nivel de tensión
            }
            
            # Agregar GRUPO solo para EXPANSION
            if self.tipo_estructura == 'EXPANSION':
                norma_registro['GRUPO'] = 'NODO ELECTRICO'
            
            datos_norma.append(norma_registro)
        
        return datos_norma
    
    def _calcular_cantidad(self, datos_excel: Dict) -> str:
        """Calcula CANTIDAD basado directamente en el campo Altura del Excel (mapeado como CANTIDAD)"""
        # El campo Altura del Excel ya viene mapeado como CANTIDAD
        if 'CANTIDAD' in datos_excel and datos_excel['CANTIDAD']:
            try:
                # Convertir a número y luego a string para limpiar formato
                cantidad_valor = float(datos_excel['CANTIDAD'])
                return str(int(cantidad_valor))  # Convertir a entero para eliminar decimales
            except (ValueError, TypeError):
                pass
        
        # Si no hay valor de CANTIDAD, devolver valor por defecto
        return '1'

# Función principal del servicio
def procesar_estructura_completo(proceso_id: str) -> None:
    """Función principal que orquesta todo el procesamiento"""
    proceso = ProcesoEstructura.objects.get(id=proceso_id)
    
    try:
        print(f"Iniciando procesamiento del proceso {proceso_id}")
        
        # 1. Procesar Excel
        proceso.estado = 'PROCESANDO'
        proceso.save()
        
        processor = ExcelProcessor(proceso)
        datos, campos_faltantes_excel = processor.procesar_archivo()
        
        if campos_faltantes_excel:
            proceso.estado = 'ERROR'
            proceso.errores = [f"Campos faltantes en Excel: {', '.join(campos_faltantes_excel)}"]
            proceso.save()
            print(f"Error: campos faltantes {campos_faltantes_excel}")
            return
        
        # 2. Transformar datos a estructura de salida
        # Para clasificación automática, usamos EXPANSION como tipo base
        transformer = DataTransformer('EXPANSION')
        datos_transformados = transformer.transformar_datos(datos)
        
        # 3. Almacenar datos transformados en el proceso
        proceso.registros_totales = len(datos_transformados)
        proceso.datos_excel = datos_transformados
        
        # 4. Mapear a norma (usando el circuito del proceso)
        # Para clasificación automática, usamos EXPANSION como tipo base
        mapper = DataMapper('EXPANSION')
        datos_norma = mapper.mapear_a_norma(datos_transformados, proceso.circuito or "")
        
        # 5. Aplicar clasificación inicial
        clasificador = ClasificadorEstructuras()
        datos_clasificados = []
        for registro in datos_norma:
            registro_clasificado = clasificador.clasificar_estructura(registro)
            datos_clasificados.append(registro_clasificado)
        
        proceso.datos_norma = datos_clasificados
        
        # 6. Detectar campos faltantes para completar
        campos_faltantes = {'CIRCUITO': list(range(len(datos_transformados)))}  # Siempre falta circuito
        
        # ESTADO_SALUD siempre se debe completar por el usuario ya que no suele venir en archivos Excel
        # o viene como información técnica incorrecta (como "Nivel de Tension")
        campos_faltantes['ESTADO_SALUD'] = list(range(len(datos_transformados)))
        
        proceso.campos_faltantes = campos_faltantes
        proceso.registros_procesados = proceso.registros_totales
        proceso.estado = 'COMPLETANDO_DATOS'
        proceso.save()
        
        print(f"Procesamiento completado: {len(datos_transformados)} registros transformados")
        
    except Exception as e:
        proceso.estado = 'ERROR'
        proceso.errores = [str(e)]
        proceso.save()
        print(f"Error en procesamiento: {str(e)}")
        raise


class FileGenerator:
    """Genera archivos TXT y XML a partir de datos transformados"""
    
    def __init__(self, proceso):
        self.proceso = proceso
        self.base_path = os.path.join(settings.MEDIA_ROOT, 'generated')
        os.makedirs(self.base_path, exist_ok=True)
        self.clasificador = ClasificadorEstructuras()

    def _extraer_fid_rep(self, registro: Dict) -> str:
        """
        Extrae el valor de 'Código FID_rep' de un registro probando varias claves
        y normalizando el resultado. Retorna cadena vacía si no existe o es inválido.
        """
        # 1. Comprobar claves explícitas comunes
        explicit_keys = ['Código FID_rep', 'Codigo FID_rep', 'CODIGO_FID_REP', 'codigo_fid_rep', 'FID_ANTERIOR', 'FID']
        for k in explicit_keys:
            if k in registro:
                v = registro.get(k)
                if v is None:
                    continue
                vs = str(v).strip()
                if vs.lower() in ('', 'nan', 'none'):
                    continue
                return vs

        # 2. Buscar cualquier clave cuyo nombre normalizado contenga 'fid' (aceptar variantes)
        try:
            for key in registro.keys():
                if not isinstance(key, str):
                    continue
                key_norm = self._normalize_col_name(key)
                if 'fid' in key_norm:
                    v = registro.get(key)
                    if v is None:
                        continue
                    vs = str(v).strip()
                    if vs.lower() in ('', 'nan', 'none'):
                        continue
                    return vs
        except Exception:
            pass

        return ''
    
    def _limpiar_valor_para_txt(self, valor):
        """
        Limpia un valor para que no contenga caracteres problemáticos en el archivo TXT
        """
        return DataUtils.limpiar_valor_para_txt(valor)
    
    def _validar_campos_criticos(self, registro):
        """
        Valida que los campos críticos tengan valores válidos usando utilidades centralizadas
        """
        # Usar valores por defecto centralizados
        campos_criticos = {
            'COORDENADA_X': '0',
            'COORDENADA_Y': '0', 
            'LONGITUD': '0',
            'LATITUD': '0',
            'GRUPO': DataUtils.VALORES_DEFECTO['GRUPO'],
            'TIPO': DataUtils.VALORES_DEFECTO['TIPO'],
            'CLASE': 'SIN_CLASE',
            'USO': 'SIN_USO',
            'ESTADO': 'ACTIVO',
            'PROPIETARIO': 'SIN_PROPIETARIO',
            'PORCENTAJE_PROPIEDAD': DataUtils.VALORES_DEFECTO['PORCENTAJE_PROPIEDAD'],
            'TIPO_PROYECTO': DataUtils.VALORES_DEFECTO['TIPO_PROYECTO'],
            'FECHA_INSTALACION': DataUtils.VALORES_DEFECTO['FECHA_DEFAULT'],
            'FECHA_OPERACION': DataUtils.VALORES_DEFECTO['FECHA_DEFAULT']
        }
        
        for campo, valor_defecto in campos_criticos.items():
            if not registro.get(campo) or str(registro.get(campo, '')).strip() == '':
                registro[campo] = valor_defecto
        
        return registro
    
    def _validar_tipos_datos(self, registro):
        """
        Valida que los campos tengan los tipos de datos correctos para carga masiva
        """
        # Campos que deben ser numéricos
        campos_numericos = {
            'COORDENADA_X': 'decimal',
            'COORDENADA_Y': 'decimal', 
            'LONGITUD': 'decimal',
            'LATITUD': 'decimal',
            'PORCENTAJE_PROPIEDAD': 'entero',
            'CANTIDAD': 'entero'
        }
        
        # Campos que deben ser fechas
        campos_fecha = {
            'FECHA_INSTALACION': 'DD/MM/YYYY',
            'FECHA_OPERACION': 'DD/MM/YYYY'
        }
        
        # Validar campos numéricos
        for campo, tipo in campos_numericos.items():
            if campo in registro and registro[campo]:
                try:
                    valor = str(registro[campo]).replace(',', '.')
                    if tipo == 'decimal':
                        float(valor)
                    elif tipo == 'entero':
                        int(float(valor))
                    # Normalizar formato decimal
                    if tipo == 'decimal':
                        registro[campo] = f"{float(valor):.6f}".rstrip('0').rstrip('.')
                    else:
                        registro[campo] = str(int(float(valor)))
                except (ValueError, TypeError):
                    # Asignar valor por defecto si no se puede convertir
                    registro[campo] = '0' if tipo == 'entero' else '0.0'
        
        # Validar campos de fecha usando utilidad centralizada
        for campo, formato in campos_fecha.items():
            if campo in registro and registro[campo]:
                registro[campo] = DataUtils.formatear_fecha(registro[campo])
        
        return registro
    
    def _get_datos_completos(self):
        """Combina datos del Excel con datos procesados (clasificación y propietario)"""
        if not self.proceso.datos_excel:
            raise Exception("No hay datos originales del Excel")
        
        datos_salida = []
        
        # Si tenemos datos_norma (datos procesados), usarlos como base
        if self.proceso.datos_norma:
            print(f"Combinando datos_excel ({len(self.proceso.datos_excel)}) con datos_norma ({len(self.proceso.datos_norma)})")
            
            for i, registro_excel in enumerate(self.proceso.datos_excel):
                # Empezar con los datos originales del Excel
                registro_completo = registro_excel.copy()
                
                # Si hay datos procesados correspondientes, usar campos específicos de allí
                if i < len(self.proceso.datos_norma):
                    registro_norma = self.proceso.datos_norma[i]
                    
                    # Campos que deben venir de datos_norma (procesados)
                    # NOTA: GRUPO NO se incluye aquí porque para TXT de expansión debe venir del Excel
                    campos_procesados = [
                        'TIPO', 'CLASE', 'USO', 'PROPIETARIO', 
                        'PORCENTAJE_PROPIEDAD', 'FECHA_OPERACION',
                        'CODIGO_MATERIAL', 'FECHA_INSTALACION', 'ESTADO_SALUD'
                    ]
                    
                    for campo in campos_procesados:
                        if campo in registro_norma:
                            registro_completo[campo] = registro_norma[campo]
                    
                    # TIPO_PROYECTO: Priorizar datos_excel (ya convertido correctamente)
                    if 'TIPO_PROYECTO' in registro_excel and registro_excel['TIPO_PROYECTO']:
                        registro_completo['TIPO_PROYECTO'] = registro_excel['TIPO_PROYECTO']
                    elif 'TIPO_PROYECTO' in registro_norma and registro_norma['TIPO_PROYECTO']:
                        registro_completo['TIPO_PROYECTO'] = registro_norma['TIPO_PROYECTO']
                    
                    # IMPORTANTE: Preservar UC del Excel original para re-clasificación
                    # Asegurar que UC esté disponible para la clasificación
                    if 'UC' in registro_excel and registro_excel['UC']:
                        registro_completo['UC'] = registro_excel['UC']
                
                # Agregar circuito del proceso
                if self.proceso.circuito:
                    registro_completo['CIRCUITO'] = self.proceso.circuito
                
                datos_salida.append(registro_completo)
        else:
            # Fallback: solo datos del Excel con valores por defecto
            print("No hay datos_norma, usando solo datos_excel con valores por defecto")
            datos_salida = self.proceso.datos_excel.copy()
            
            # Aplicar valores por defecto
            for i, registro in enumerate(datos_salida):
                if self.proceso.circuito:
                    registro['CIRCUITO'] = self.proceso.circuito
                
                # Valores por defecto básicos
                defaults = {
                    # 'GRUPO': 'ESTRUCTURAS EYT',  # COMENTADO: Para EXPANSION usar valor del Excel
                    'TIPO': 'SECUNDARIO',  # Por defecto según reglas de negocio
                    'CLASE': 'POSTE',
                    'USO': 'DISTRIBUCION ENERGIA',
                    'PORCENTAJE_PROPIEDAD': '100'
                }
                
                # Aplicar propietario definido por el usuario (solo para ciertos tipos)
                # NOTA: Para estructuras clasificadas como EXPANSION, PROPIETARIO debe venir del campo "Nombre" del Excel
                # Como ahora tenemos clasificación automática, verificamos si hay estructuras de expansión
                tiene_expansion = any(
                    'EXPANSION' in str(registro.get('TIPO_PROYECTO', '')).upper() 
                    for registro in datos_salida
                )
                if self.proceso.propietario_definido and not tiene_expansion:
                    registro['PROPIETARIO'] = self.proceso.propietario_definido
                
                # Aplicar valores por defecto solo si el campo no existe o está vacío
                for campo, valor_default in defaults.items():
                    if campo not in registro or not registro[campo]:
                        registro[campo] = valor_default
        
        print(f"Datos completos preparados: {len(datos_salida)} registros")
        if datos_salida and 'PROPIETARIO' in datos_salida[0]:
            print(f"Propietario en datos finales: {datos_salida[0]['PROPIETARIO']}")
        
        return datos_salida

    def _preparar_datos_finales(self, datos_salida):
        """
        Prepara los datos finales aplicando todas las transformaciones necesarias
        antes de generar los archivos.
        
        Este método centraliza toda la lógica de preparación final siguiendo
        el principio de responsabilidad única.
        """
        datos_preparados = []
        
        for registro in datos_salida:
            registro_final = registro.copy()
            
            # 1. Aplicar ESTADO_SALUD del proceso si fue definido por el usuario
            if (hasattr(self.proceso, 'estado_salud_definido') and 
                self.proceso.estado_salud_definido and 
                self.proceso.estado_salud_definido != 'None'):
                registro_final['ESTADO_SALUD'] = self.proceso.estado_salud_definido
            elif not registro_final.get('ESTADO_SALUD'):
                # Si ESTADO_SALUD está vacío y no fue definido por el usuario, 
                # marcar que se requiere completar
                print("ADVERTENCIA: ESTADO_SALUD vacío en registro, se requiere completar por el usuario")
            
            # 1b. Aplicar ESTADO del proceso - usar Excel si es válido, si no el del usuario
            estado_excel = registro_final.get('ESTADO', '').strip()
            estados_validos = ['CONSTRUCCION', 'RETIRADO', 'OPERACION']
            
            if estado_excel and estado_excel in estados_validos:
                # Si el Excel trae un estado válido, usarlo
                registro_final['ESTADO'] = estado_excel
            elif (hasattr(self.proceso, 'estado_estructura_definido') and 
                  self.proceso.estado_estructura_definido and 
                  self.proceso.estado_estructura_definido != 'None'):
                # Si no hay estado válido en Excel, usar el seleccionado por el usuario
                registro_final['ESTADO'] = self.proceso.estado_estructura_definido
            else:
                # Si no hay ninguno, usar OPERACION por defecto
                registro_final['ESTADO'] = 'OPERACION'
            
            # 2. Asegurar TIPO_PROYECTO - preservar valor de datos_excel si existe
            if not registro_final.get('TIPO_PROYECTO'):
                # El valor ya debería estar convertido correctamente en el proceso de transformación
                # Solo como fallback, generar desde UC
                uc = registro_final.get('UC', '')
                if uc:
                    tipo_proyecto = self.clasificador._generar_tipo_proyecto_desde_nivel_tension(uc)
                    if tipo_proyecto:
                        registro_final['TIPO_PROYECTO'] = tipo_proyecto
            
            # 3. Asegurar que las fechas estén en el formato correcto
            for campo_fecha in ['FECHA_INSTALACION', 'FECHA_OPERACION']:
                if campo_fecha in registro_final and registro_final[campo_fecha]:
                    registro_final[campo_fecha] = self.clasificador._formatear_fecha(
                        registro_final[campo_fecha]
                    )
            
            # 4. Asegurar ID_MERCADO siempre sea 161 (valor constante del sistema)
            registro_final['ID_MERCADO'] = '161'
            
            # 5. Limpiar campos que deben ir vacíos
            # OT_MAXIMO debe ir vacío ya que el Excel no trae información válida para este campo
            registro_final['OT_MAXIMO'] = ''
            
            # 5b. Asegurar SALINIDAD siempre sea "NO" (valor constante del sistema)
            registro_final['SALINIDAD'] = 'NO'
            
            # 6. Preservar CLASIFICACION_MERCADO que ya viene mapeado desde el campo Poblacion del Excel
            # El campo CLASIFICACION_MERCADO ya se mapeó correctamente desde "Poblacion" en la transformación inicial
            # Solo necesitamos asegurar que se preserve el valor existente
            if not registro_final.get('CLASIFICACION_MERCADO'):
                registro_final['CLASIFICACION_MERCADO'] = ''
            
            # 6b. Corregir TIPO_ADECUACION para quitar tildes (requerimiento del aplicativo)
            tipo_adecuacion = registro_final.get('TIPO_ADECUACION', '')
            if tipo_adecuacion:
                conversiones_tipo_adecuacion = {
                    'RETENCIÓN': 'RETENCION',
                    'SUSPENSIÓN': 'SUSPENSION',
                    'retención': 'RETENCION',
                    'suspensión': 'SUSPENSION',
                    'Retención': 'RETENCION',
                    'Suspensión': 'SUSPENSION'
                }
                registro_final['TIPO_ADECUACION'] = conversiones_tipo_adecuacion.get(
                    tipo_adecuacion, tipo_adecuacion.upper()
                )
            
            # 7. REGLA CRÍTICA: EMPRESA debe tener exactamente el mismo valor que PROPIETARIO
            propietario_valor = registro_final.get('PROPIETARIO', '')
            registro_final['EMPRESA'] = propietario_valor
            
            # 8. REGLA CRÍTICA: GRUPO debe ser siempre "ESTRUCTURAS EYT" (no viene del Excel)
            registro_final['GRUPO'] = 'ESTRUCTURAS EYT'
            
            # 9. Aplicar valores por defecto para campos críticos vacíos
            valores_defecto = {
                'TIPO': 'PRIMARIO',  # Cambiado de SECUNDARIO a PRIMARIO
                'CLASE': 'POSTE',
                'USO': 'DISTRIBUCION ENERGIA',
                'PORCENTAJE_PROPIEDAD': '100',
                'ESTADO': '',  # Campo ESTADO debe estar vacío según el formato
            }
            
            for campo, valor_defecto in valores_defecto.items():
                if campo not in registro_final or not registro_final[campo]:
                    registro_final[campo] = valor_defecto
            
            datos_preparados.append(registro_final)
        
        return datos_preparados

    def generar_txt(self):
        """Genera archivo TXT con los datos transformados (estructura completa)"""
        try:
            filename = f"estructuras_{self.proceso.id}.txt"
            filepath = os.path.join(self.base_path, filename)
            
            # Obtener datos completos con campos aplicados
            datos_salida = self._get_datos_completos()
            
            if not datos_salida:
                raise Exception("No hay datos transformados para generar archivo TXT")
            
            # APLICAR PREPARACIÓN FINAL DE DATOS
            datos_finales = self._preparar_datos_finales(datos_salida)
            
            # REGLA ESPECIAL PARA FID_ANTERIOR basada en TIPO_PROYECTO
            # Solo aplica al TXT de expansión, no al XML
            incluir_fid_anterior = self._debe_incluir_fid_anterior(datos_finales)
            
            # Nombres definitivos de encabezados
            encabezados_base = [
                'COORDENADA_X', 'COORDENADA_Y', 'GRUPO', 'TIPO', 'CLASE', 'USO', 'ESTADO', 
                'TIPO_ADECUACION', 'PROPIETARIO', 'PORCENTAJE_PROPIEDAD', 'UBICACION',
                'CODIGO_MATERIAL', 'FECHA_INSTALACION', 'FECHA_OPERACION', 'PROYECTO',
                'EMPRESA', 'OBSERVACIONES', 'CLASIFICACION_MERCADO', 'TIPO_PROYECTO',
                'ID_MERCADO', 'UC', 'ESTADO_SALUD', 'OT_MAXIMO', 'CODIGO_MARCACION',
                'SALINIDAD'
            ]
            
            # Agregar FID_ANTERIOR solo si debe incluirse
            if incluir_fid_anterior:
                encabezados_base.append('FID_ANTERIOR')
            
            encabezados_base.append('ENLACE')
            encabezados = encabezados_base
            
            # Mapeo de campos internos a encabezados
            campos_orden_base = [
                'COORDENADA_X', 'COORDENADA_Y', 'GRUPO', 'TIPO', 'CLASE', 'USO', 'ESTADO', 
                'TIPO_ADECUACION', 'PROPIETARIO', 'PORCENTAJE_PROPIEDAD', 'UBICACION',
                'CODIGO_MATERIAL', 'FECHA_INSTALACION', 'FECHA_OPERACION', 'PROYECTO',
                'EMPRESA', 'OBSERVACIONES', 'CLASIFICACION_MERCADO', 'TIPO_PROYECTO',
                'ID_MERCADO', 'UC', 'ESTADO_SALUD', 'OT_MAXIMO', 'CODIGO_MARCACION',
                'SALINIDAD'
            ]
            
            # Agregar FID_ANTERIOR solo si debe incluirse
            if incluir_fid_anterior:
                campos_orden_base.append('FID_ANTERIOR')
            
            campos_orden_base.append('ENLACE')
            campos_orden = campos_orden_base

            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                # Escribir encabezados definitivos separados por |
                f.write('|'.join(encabezados) + '\n')
                
                # Escribir datos separados por |
                for registro in datos_finales:
                    # Validar y corregir campos críticos
                    registro_validado = self._validar_campos_criticos(registro.copy())
                    
                    # Validar tipos de datos
                    registro_validado = self._validar_tipos_datos(registro_validado)
                    
                    valores = []
                    for campo in campos_orden:
                        valor = registro_validado.get(campo, '')
                        # IMPORTANTE: Limpiar el valor antes de agregarlo
                        valor_limpio = self._limpiar_valor_para_txt(valor)
                        valores.append(valor_limpio)
                    f.write('|'.join(valores) + '\n')
            
            # Validar el archivo generado
            self._validar_archivo_txt(filepath)
            
            return filename
            
        except Exception as e:
            raise Exception(f"Error generando archivo TXT: {str(e)}")

    def _normalize_col_name(self, s):
        if s is None:
            return ''
        ns = str(s)
        ns = ns.replace('\n', ' ').replace('\r', ' ')
        ns = ns.replace('_', ' ')
        ns = re.sub(r"\s+", ' ', ns)
        ns = ns.strip().lower()
        trans = str.maketrans('áéíóúÁÉÍÓÚ', 'aeiouAEIOU')
        ns = ns.translate(trans)
        return ns

    def generar_txt_baja(self):
        """
        Genera archivo TXT con datos filtrados por 'Código FID_rep' válido,
        siguiendo exactamente el mismo flujo que generar_txt()
        """
        try:
            filename = f"estructuras_{self.proceso.id}_baja.txt"
            filepath = os.path.join(self.base_path, filename)
            
            # 1. FILTRAR PRIMERO los datos_excel por Código FID_rep
            if not self.proceso.datos_excel:
                raise Exception("No hay datos del Excel para filtrar")
            
            datos_excel_filtrados = []
            indices_filtrados = []
            
            for i, registro in enumerate(self.proceso.datos_excel):
                fid_rep = self._extraer_fid_rep(registro)
                if fid_rep:
                    datos_excel_filtrados.append(registro)
                    indices_filtrados.append(i)
            
            print(f"DEBUG: Encontrados {len(datos_excel_filtrados)} registros con Código FID_rep válido de {len(self.proceso.datos_excel)} totales")
            
            if not datos_excel_filtrados:
                print("ADVERTENCIA: No hay registros con 'Código FID_rep' válido en 'proceso.datos_excel', intentaremos reprocesar desde el archivo Excel original antes de devolver un archivo vacío.")
            
            # 2. Construir datos_salida_filtrados directamente a partir de los índices
            datos_excel_originales = self.proceso.datos_excel
            datos_norma_originales = self.proceso.datos_norma if hasattr(self.proceso, 'datos_norma') else None

            datos_salida_filtrados = []
            campos_procesados = [
                'TIPO', 'CLASE', 'USO', 'PROPIETARIO',
                'PORCENTAJE_PROPIEDAD', 'FECHA_OPERACION',
                'CODIGO_MATERIAL', 'FECHA_INSTALACION', 'ESTADO_SALUD'
            ]

            for idx in indices_filtrados:
                if idx >= len(datos_excel_originales):
                    continue
                registro_excel = datos_excel_originales[idx].copy()

                # Si existen datos_norma, sobreescribir campos procesados equivalentes
                if datos_norma_originales and idx < len(datos_norma_originales):
                    registro_norma = datos_norma_originales[idx]
                    for campo in campos_procesados:
                        if campo in registro_norma and registro_norma[campo] not in (None, ''):
                            registro_excel[campo] = registro_norma[campo]

                # Agregar circuito si aplica
                if hasattr(self.proceso, 'circuito') and self.proceso.circuito:
                    registro_excel['CIRCUITO'] = self.proceso.circuito

                datos_salida_filtrados.append(registro_excel)

            print(f"DEBUG generar_txt_baja: construidos datos_salida_filtrados={len(datos_salida_filtrados)}")

            # Si la lista quedó vacía, intentar re-procesar el Excel original directamente
            if not datos_salida_filtrados:
                print("DEBUG generar_txt_baja: no se encontraron registros filtrados en 'proceso.datos_excel', intentando reprocesar desde el archivo Excel original...")
                try:
                    processor = ExcelProcessor(self.proceso)
                    raw_datos, campos_faltantes = processor.procesar_archivo()
                    if campos_faltantes:
                        print(f"DEBUG generar_txt_baja: reprocesar desde Excel devolvió campos faltantes: {campos_faltantes}")
                        raw_datos = []

                    # Filtrar raw_datos por FID (buscar columnas cuyo nombre normalizado contenga 'fid')
                    raw_filtrados = []
                    for registro in raw_datos:
                        # DEBUG: mostrar claves que contienen 'fid' y su valor para este registro
                        try:
                            fid_candidates = []
                            if isinstance(registro, dict):
                                for k, v in registro.items():
                                    try:
                                        if isinstance(k, str) and 'fid' in self._normalize_col_name(k):
                                            fid_candidates.append((k, v))
                                    except Exception:
                                        continue
                            if fid_candidates:
                                print('DEBUG generar_txt_baja: posibles campos FID en registro:', fid_candidates[:3])
                        except Exception:
                            pass
                        fid = ''
                        if isinstance(registro, dict):
                            # Buscar claves que, normalizadas, contengan 'fid' (aceptar variantes como 'Código FID\nGIT' o 'Código FID_rep')
                            for k, v in registro.items():
                                try:
                                    if not isinstance(k, str):
                                        continue
                                    key_norm = self._normalize_col_name(k)
                                    if 'fid' in key_norm:
                                        if v not in (None, '') and str(v).strip().lower() not in ('', 'nan', 'none'):
                                            fid = str(v).strip()
                                            break
                                except Exception:
                                    continue

                        # Como medida adicional, también revisar claves exactas conocidas
                        if not fid and isinstance(registro, dict):
                            for n in ['Código FID_rep', 'Codigo FID_rep', 'CODIGO_FID_REP', 'codigo_fid_rep']:
                                if n in registro and registro.get(n) not in (None, '') and str(registro.get(n)).strip().lower() not in ('', 'nan', 'none'):
                                    fid = str(registro.get(n)).strip()
                                    break

                        if fid:
                            try:
                                registro['FID_ANTERIOR'] = fid
                            except Exception:
                                pass
                            raw_filtrados.append(registro)

                    print(f"DEBUG generar_txt_baja: raw_filtrados desde Excel = {len(raw_filtrados)}")

                    if raw_filtrados:
                        # Transformar raw_filtrados a la estructura de salida
                        transformer = DataTransformer('EXPANSION')
                        datos_transformados_filtrados = transformer.transformar_datos(raw_filtrados)
                        mapper = DataMapper('EXPANSION')
                        datos_norma_filtrados = mapper.mapear_a_norma(datos_transformados_filtrados, self.proceso.circuito or "")

                        # Construir datos_salida_filtrados combinando transformados y norma filtrados
                        campos_procesados = [
                            'TIPO', 'CLASE', 'USO', 'PROPIETARIO',
                            'PORCENTAJE_PROPIEDAD', 'FECHA_OPERACION',
                            'CODIGO_MATERIAL', 'FECHA_INSTALACION', 'ESTADO_SALUD'
                        ]
                        for i, registro_tr in enumerate(datos_transformados_filtrados):
                            registro_comb = registro_tr.copy()
                            if i < len(datos_norma_filtrados):
                                reg_norm = datos_norma_filtrados[i]
                                for campo in campos_procesados:
                                    if campo in reg_norm and reg_norm[campo] not in (None, ''):
                                        registro_comb[campo] = reg_norm[campo]
                            # Transferir el FID detectado en el raw original si existe
                            try:
                                raw_original = raw_filtrados[i] if i < len(raw_filtrados) else None
                                if raw_original and isinstance(raw_original, dict):
                                    fid_val = raw_original.get('FID_ANTERIOR') or raw_original.get('Código FID_rep') or raw_original.get('Codigo FID_rep')
                                    if fid_val and str(fid_val).strip().lower() not in ('', 'nan', 'none'):
                                        registro_comb['FID_ANTERIOR'] = str(fid_val).strip()
                            except Exception:
                                pass
                            if self.proceso.circuito:
                                registro_comb['CIRCUITO'] = self.proceso.circuito
                            datos_salida_filtrados.append(registro_comb)

                except Exception as e:
                    print(f"DEBUG generar_txt_baja: reprocesado falló: {e}")

            if not datos_salida_filtrados:
                raise Exception("No hay datos transformados (filtrados) para generar archivo TXT de baja")

            # 3. APLICAR PREPARACIÓN FINAL DE DATOS sobre los registros filtrados
            datos_finales = self._preparar_datos_finales(datos_salida_filtrados)

            # 3b. FILTRAR DEFINITIVAMENTE registros que no tengan FID (asegurarnos solo exportar los que tienen 'Código FID_rep')
            datos_finales_filtrados = []
            for registro in datos_finales:
                try:
                    # _extraer_fid_rep verifica varias claves; además admitimos FID_ANTERIOR si existe
                    tiene_fid = False
                    if self._extraer_fid_rep(registro):
                        tiene_fid = True
                    elif registro.get('FID_ANTERIOR') and str(registro.get('FID_ANTERIOR')).strip().lower() not in ('', 'nan', 'none'):
                        tiene_fid = True

                    if tiene_fid:
                        datos_finales_filtrados.append(registro)
                except Exception:
                    # En caso de error de validación, no incluir el registro
                    continue

            print(f"DEBUG generar_txt_baja: len(datos_finales) antes_filtrado={len(datos_finales)}, despues_filtrado={len(datos_finales_filtrados)}")

            if not datos_finales_filtrados:
                raise Exception("No hay registros con 'Código FID_rep' válidos para exportar en el TXT de baja")

            datos_finales = datos_finales_filtrados
            
            # 5. REGLA ESPECIAL PARA FID_ANTERIOR (IGUAL que generar_txt)
            incluir_fid_anterior = self._debe_incluir_fid_anterior(datos_finales)
            
            # 6. Nombres definitivos de encabezados (IGUAL que generar_txt)
            encabezados_base = [
                'COORDENADA_X', 'COORDENADA_Y', 'GRUPO', 'TIPO', 'CLASE', 'USO', 'ESTADO', 
                'TIPO_ADECUACION', 'PROPIETARIO', 'PORCENTAJE_PROPIEDAD', 'UBICACION',
                'CODIGO_MATERIAL', 'FECHA_INSTALACION', 'FECHA_OPERACION', 'PROYECTO',
                'EMPRESA', 'OBSERVACIONES', 'CLASIFICACION_MERCADO', 'TIPO_PROYECTO',
                'ID_MERCADO', 'UC', 'ESTADO_SALUD', 'OT_MAXIMO', 'CODIGO_MARCACION',
                'SALINIDAD'
            ]
            
            # Agregar FID_ANTERIOR solo si debe incluirse (IGUAL que generar_txt)
            if incluir_fid_anterior:
                encabezados_base.append('FID_ANTERIOR')
            
            encabezados_base.append('ENLACE')
            encabezados = encabezados_base
            
            # 7. Mapeo de campos internos a encabezados (IGUAL que generar_txt)
            campos_orden_base = [
                'COORDENADA_X', 'COORDENADA_Y', 'GRUPO', 'TIPO', 'CLASE', 'USO', 'ESTADO', 
                'TIPO_ADECUACION', 'PROPIETARIO', 'PORCENTAJE_PROPIEDAD', 'UBICACION',
                'CODIGO_MATERIAL', 'FECHA_INSTALACION', 'FECHA_OPERACION', 'PROYECTO',
                'EMPRESA', 'OBSERVACIONES', 'CLASIFICACION_MERCADO', 'TIPO_PROYECTO',
                'ID_MERCADO', 'UC', 'ESTADO_SALUD', 'OT_MAXIMO', 'CODIGO_MARCACION',
                'SALINIDAD'
            ]
            
            # Agregar FID_ANTERIOR solo si debe incluirse (IGUAL que generar_txt)
            if incluir_fid_anterior:
                campos_orden_base.append('FID_ANTERIOR')
            
            campos_orden_base.append('ENLACE')
            campos_orden = campos_orden_base

            # 8. Escribir archivo (IGUAL que generar_txt)
            # DEBUG: inspeccionar datos antes de escribir
            print("DEBUG generar_txt_baja: len(datos_excel_filtrados)=", len(datos_excel_filtrados))
            print("DEBUG generar_txt_baja: indices_filtrados=", indices_filtrados[:10])
            print("DEBUG generar_txt_baja: len(datos_salida_filtrados)=", len(datos_salida_filtrados))
            print("DEBUG generar_txt_baja: ejemplo datos_salida_filtrados[0] (si existe)=", datos_salida_filtrados[0] if datos_salida_filtrados else None)
            print("DEBUG generar_txt_baja: len(datos_finales)=", len(datos_finales))
            if datos_finales:
                sample = datos_finales[0]
                print("DEBUG generar_txt_baja: ejemplo campos del primer registro:", {k: sample.get(k) for k in ['COORDENADA_X','COORDENADA_Y','UC','PROYECTO','ENLACE']})

            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                # Escribir encabezados definitivos separados por |
                f.write('|'.join(encabezados) + '\n')
                
                # Escribir datos separados por |
                for registro in datos_finales:
                    # Validar y corregir campos críticos (IGUAL que generar_txt)
                    registro_validado = self._validar_campos_criticos(registro.copy())
                    
                    # Validar tipos de datos (IGUAL que generar_txt)
                    registro_validado = self._validar_tipos_datos(registro_validado)
                    
                    valores = []
                    for campo in campos_orden:
                        valor = registro_validado.get(campo, '')
                        # IMPORTANTE: Limpiar el valor antes de agregarlo (IGUAL que generar_txt)
                        valor_limpio = self._limpiar_valor_para_txt(valor)
                        valores.append(valor_limpio)
                    f.write('|'.join(valores) + '\n')
            
            # 9. RESTAURAR datos originales del proceso
            self.proceso.datos_excel = datos_excel_originales
            self.proceso.datos_norma = datos_norma_originales
            
            # 10. Validar el archivo generado (IGUAL que generar_txt)
            self._validar_archivo_txt(filepath)
            
            print(f"Archivo TXT de baja generado exitosamente: {filename} con {len(datos_finales)} registros")
            return filename
            
        except Exception as e:
            # Asegurar que se restauren los datos originales en caso de error
            if 'datos_excel_originales' in locals():
                self.proceso.datos_excel = datos_excel_originales
            if 'datos_norma_originales' in locals():
                self.proceso.datos_norma = datos_norma_originales
            raise Exception(f"Error generando archivo TXT de baja: {str(e)}")

    def _tiene_fid_en_registro(self, registro: Dict) -> bool:
        """
        Determina si un registro contiene un FID válido examinando varias claves.
        """
        try:
            # 1. Revisar claves explícitas
            for key in registro.keys():
                if not isinstance(key, str):
                    continue
                k = key.strip().lower()
                if 'fid' in k:
                    val = registro.get(key)
                    if val is None:
                        continue
                    if str(val).strip().lower() in ('', 'nan', 'none'):
                        continue
                    return True

            # 2. Revisar claves normalizadas (p.ej. 'codigo fid_rep' con saltos de línea)
            for key, val in registro.items():
                try:
                    if not isinstance(key, str):
                        continue
                    kn = self._normalize_col_name(key)
                    if 'fid' in kn:
                        if val not in (None, '') and str(val).strip().lower() not in ('', 'nan', 'none'):
                            return True
                except Exception:
                    continue

            # 3. Revisar FID_ANTERIOR específicamente
            if 'FID_ANTERIOR' in registro and registro.get('FID_ANTERIOR') not in (None, ''):
                if str(registro.get('FID_ANTERIOR')).strip().lower() not in ('', 'nan', 'none'):
                    return True

            return False
        except Exception:
            return False

    def generar_xml_baja(self):
        """
        Genera archivo XML de configuración para registros con 'Código FID_rep' válido,
        siguiendo exactamente el mismo flujo que generar_xml()
        """
        try:
            from xml.etree.ElementTree import Element, SubElement, tostring
            from xml.dom import minidom
            
            filename = f"estructuras_{self.proceso.id}_baja.xml"
            filepath = os.path.join(self.base_path, filename)
            
            # 1. FILTRAR PRIMERO los datos_excel por Código FID_rep (para contar)
            if not self.proceso.datos_excel:
                raise Exception("No hay datos del Excel para filtrar")
            
            registros_con_fid = 0
            for registro in self.proceso.datos_excel:
                fid_rep = self._extraer_fid_rep(registro)
                if fid_rep:
                    registros_con_fid += 1
            
            print(f"DEBUG: XML de baja - {registros_con_fid} registros con Código FID_rep válido de {len(self.proceso.datos_excel)} totales")
            
            # 2. Crear estructura XML según especificación (IGUAL que generar_xml)
            root = Element('Configuracion')
            
            # Elemento principal (IGUAL que generar_xml)
            elemento = SubElement(root, 'Elemento')
            elemento.text = 'Poste'
            
            # Contenedor de campos (IGUAL que generar_xml)
            campos = SubElement(root, 'Campos')
            
            # 3. Definición de campos EXACTA según generar_xml funcional
            campos_config = [
                {'nombre': 'GRUPO', 'componente': 'EPOSTE_AT', 'atributo': 'GRUPO'},
                {'nombre': 'TIPO', 'componente': 'EPOSTE_AT', 'atributo': 'TIPO'},
                {'nombre': 'CLASE', 'componente': 'EPOSTE_AT', 'atributo': 'CLASE'},
                {'nombre': 'USO', 'componente': 'EPOSTE_AT', 'atributo': 'USO'},
                {'nombre': 'ESTADO', 'componente': 'CCOMUN', 'atributo': 'ESTADO'},
                {'nombre': 'TIPO_ADECUACION', 'componente': 'EPOSTE_AT', 'atributo': 'TIPO_ADECUACION'},
                {'nombre': 'PROPIETARIO', 'componente': 'CPROPIETARIO', 'atributo': 'PROPIETARIO_1'},
                {'nombre': 'PORCENTAJE_PROPIEDAD', 'componente': 'CPROPIETARIO', 'atributo': 'PORCENTAJE_PROP_1'},
                {'nombre': 'UBICACION', 'componente': 'CCOMUN', 'atributo': 'UBICACION'},
                {'nombre': 'CODIGO_MATERIAL', 'componente': 'CCOMUN', 'atributo': 'CODIGO_MATERIAL'},
                {'nombre': 'FECHA_INSTALACION', 'componente': 'CCOMUN', 'atributo': 'FECHA_INSTALACION'},
                {'nombre': 'FECHA_OPERACION', 'componente': 'CCOMUN', 'atributo': 'FECHA_OPERACION'},
                {'nombre': 'PROYECTO', 'componente': 'CCOMUN', 'atributo': 'PROYECTO'},
                {'nombre': 'EMPRESA', 'componente': 'CCOMUN', 'atributo': 'EMPRESA_ORIGEN'},
                {'nombre': 'OBSERVACIONES', 'componente': 'CCOMUN', 'atributo': 'OBSERVACIONES'},
                {'nombre': 'CLASIFICACION_MERCADO', 'componente': 'CCOMUN', 'atributo': 'CLASIFICACION_MERCADO'},
                {'nombre': 'TIPO_PROYECTO', 'componente': 'CCOMUN', 'atributo': 'TIPO_PROYECTO'},
                {'nombre': 'ID_MERCADO', 'componente': 'CCOMUN', 'atributo': 'ID_MERCADO'},
                {'nombre': 'UC', 'componente': 'CCOMUN', 'atributo': 'UC'},
                {'nombre': 'ESTADO_SALUD', 'componente': 'CCOMUN', 'atributo': 'ESTADO_SALUD'},
                {'nombre': 'OT_MAXIMO', 'componente': 'CCOMUN', 'atributo': 'OT_MAXIMO'},
                {'nombre': 'CODIGO_MARCACION', 'componente': 'CCOMUN', 'atributo': 'CODIGO_MARCACION'},
                {'nombre': 'SALINIDAD', 'componente': 'CCOMUN', 'atributo': 'SALINIDAD'},
                {'nombre': 'G3E_GEOMETRY', 'componente': '', 'atributo': ''},
            ]

            # 4. Agregar cada campo con su número correcto (IGUAL que generar_xml)
            for i, campo_config in enumerate(campos_config):
                campo_elem = SubElement(campos, f'Campo{i}')

                nombre = SubElement(campo_elem, 'Nombre')
                nombre.text = campo_config['nombre']

                componente = SubElement(campo_elem, 'Componente')
                if campo_config['componente']:
                    componente.text = campo_config['componente']

                atributo = SubElement(campo_elem, 'Atributo')
                if campo_config['atributo']:
                    atributo.text = campo_config['atributo']

            # 5. Formatear XML con indentación bonita (IGUAL que generar_xml)
            rough_string = tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")

            # Eliminar la declaración XML <?xml version="1.0" ?> (IGUAL que generar_xml)
            lines = pretty_xml.split('\n')
            if lines[0].startswith('<?xml'):
                lines = lines[1:]
            while lines and lines[-1].strip() == '':
                lines.pop()

            pretty_xml_sin_declaracion = '\n'.join(lines)

            # 6. Escribir archivo con UTF-8 BOM (IGUAL que generar_xml)
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(pretty_xml_sin_declaracion)

            print(f"Archivo XML de baja generado exitosamente: {filename} (configuración para {registros_con_fid} registros)")
            return filename

        except Exception as e:
            raise Exception(f"Error generando archivo XML de baja: {str(e)}")
    
    def _validar_archivo_txt(self, filepath):
        """
        Valida que el archivo TXT generado esté correctamente formateado para carga masiva
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                raise Exception("El archivo está vacío")
            
            # Verificar que todas las líneas tengan el mismo número de campos
            header_fields = lines[0].strip().split('|')
            num_fields = len(header_fields)
            
            # Validaciones específicas para carga masiva
            errores = []
            
            for i, line in enumerate(lines[1:], start=2):
                line_clean = line.strip()
                if not line_clean:  # Saltar líneas vacías
                    continue
                    
                fields = line_clean.split('|')
                
                # Verificar número de campos
                if len(fields) != num_fields:
                    errores.append(f"Línea {i}: tiene {len(fields)} campos, se esperaban {num_fields}")
                
                # Verificar que no haya saltos de línea dentro de los campos
                for j, field in enumerate(fields):
                    if '\n' in field or '\r' in field:
                        errores.append(f"Línea {i}, Campo {header_fields[j]}: contiene saltos de línea")
                    
                    # Verificar que no haya pipes dentro de los campos
                    if '|' in field.replace('|', ''):  # Esto detecta pipes adicionales
                        errores.append(f"Línea {i}, Campo {header_fields[j]}: contiene separadores pipe internos")
                
                # Validar campos críticos específicos
                if len(fields) >= 2:  # Al menos coordenadas
                    try:
                        # Validar coordenadas si existen
                        coord_x = fields[0] if fields[0] else '0'
                        coord_y = fields[1] if fields[1] else '0'
                        float(coord_x.replace(',', '.'))
                        float(coord_y.replace(',', '.'))
                    except (ValueError, IndexError):
                        errores.append(f"Línea {i}: coordenadas inválidas")
            
            # Verificar encoding UTF-8
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    f.read()
            except UnicodeDecodeError:
                errores.append("El archivo contiene caracteres no UTF-8")
            
            # Verificar tamaño del archivo (no debe ser excesivamente grande)
            import os
            file_size = os.path.getsize(filepath)
            if file_size > 50 * 1024 * 1024:  # 50MB
                errores.append(f"El archivo es muy grande ({file_size/1024/1024:.1f}MB), podría causar problemas en carga masiva")
            
            if errores:
                raise Exception(f"Errores de validación encontrados: {'; '.join(errores[:5])}")  # Mostrar solo los primeros 5
            
            return True
            
        except Exception as e:
            raise Exception(f"Error validando archivo TXT: {str(e)}")
    
    def generar_resumen_archivo(self, filepath):
        """
        Genera un resumen del archivo para verificación antes de carga masiva
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                return {"error": "Archivo vacío"}
            
            header_fields = lines[0].strip().split('|')
            num_registros = len(lines) - 1  # Excluir header
            
            # Análisis básico
            resumen = {
                "archivo": os.path.basename(filepath),
                "total_registros": num_registros,
                "total_campos": len(header_fields),
                "campos": header_fields,
                "tamaño_archivo_kb": round(os.path.getsize(filepath) / 1024, 2),
                "encoding": "UTF-8",
                "separador": "|"
            }
            
            # Muestra de los primeros 3 registros
            registros_muestra = []
            for i, line in enumerate(lines[1:4], start=1):  # Primeros 3 registros
                if line.strip():
                    fields = line.strip().split('|')
                    registro_dict = {}
                    for j, field in enumerate(fields):
                        if j < len(header_fields):
                            registro_dict[header_fields[j]] = field[:50] + '...' if len(field) > 50 else field
                    registros_muestra.append(f"Registro {i}: {registro_dict}")
            
            resumen["muestra_registros"] = registros_muestra
            
            return resumen
            
        except Exception as e:
            return {"error": f"Error generando resumen: {str(e)}"}
    
    def generar_norma_txt(self):
        """Genera archivo TXT de norma con los datos transformados para cargue masivo"""
        try:
            filename = f"norma_{self.proceso.id}.txt"
            filepath = os.path.join(self.base_path, filename)
            
            # Obtener datos de norma
            if not self.proceso.datos_norma:
                raise Exception("No hay datos de norma para generar archivo")
            
            # Orden de campos para archivo de norma según especificación - ACTUALIZADO PARA COINCIDIR CON XML
            campos_orden = [
                'ENLACE', 'NORMA', 'GRUPO', 'CIRCUITO', 'CODIGO_TRAFO',
                'CANTIDAD','MACRONORMA', 'FECHA_INSTALACION', 'TIPO_ADECUACION', 'OBSERVACIONES'
            ]
            
            # Preparar datos de norma aplicando transformaciones necesarias
            datos_norma_finales = self._preparar_datos_norma_finales(self.proceso.datos_norma)
            
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                # Escribir encabezados
                f.write('|'.join(campos_orden) + '\n')
                
                # Escribir datos
                for registro in datos_norma_finales:
                    # Asegurar que todos los campos tengan al menos un valor vacío válido
                    registro_seguro = {}
                    for campo in campos_orden:
                        valor = registro.get(campo, '')
                        # Si el campo está vacío o es None, asignar valor por defecto
                        if not valor or str(valor).strip() == '':
                            if campo == 'CANTIDAD':
                                registro_seguro[campo] = '1'
                            elif campo in ['FECHA_INSTALACION']:
                                registro_seguro[campo] = '01/01/2000'
                            else:
                                registro_seguro[campo] = ''
                        else:
                            registro_seguro[campo] = valor
                    
                    valores = []
                    for campo in campos_orden:
                        valor = registro_seguro.get(campo, '')
                        # IMPORTANTE: Limpiar el valor antes de agregarlo
                        valor_limpio = self._limpiar_valor_para_txt(valor)
                        valores.append(valor_limpio)
                    f.write('|'.join(valores) + '\n')
            
            # Validar el archivo generado
            self._validar_archivo_norma_txt(filepath)
            
            return filename
            
        except Exception as e:
            raise Exception(f"Error generando archivo TXT de norma: {str(e)}")
    
    def _validar_archivo_norma_txt(self, filepath):
        """
        Valida que el archivo TXT de norma esté correctamente formateado
        """
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
                
            if len(lines) < 2:
                raise Exception("El archivo no tiene contenido suficiente")
            
            # Validar que cada línea tenga el número correcto de pipes
            num_campos = len(lines[0].strip().split('|'))
            
            for i, line in enumerate(lines[1:], start=2):
                line_stripped = line.strip()
                if not line_stripped:  # Ignorar líneas vacías
                    continue
                    
                campos = line_stripped.split('|')
                if len(campos) != num_campos:
                    print(f"Advertencia línea {i}: esperados {num_campos} campos, encontrados {len(campos)}")
                    print(f"Línea problemática: {line_stripped[:100]}...")
                    
        except Exception as e:
            print(f"Error validando archivo TXT de norma: {str(e)}")
    
    def _debe_incluir_fid_anterior(self, datos_finales):
        """
        Determina si se debe incluir la columna FID_ANTERIOR en el TXT de expansión
        
        Reglas:
        - Si es T2 o T4: La columna FID_ANTERIOR desaparece (no se incluye)
        - Si es T1 o T3: La columna FID_ANTERIOR debe estar presente
        
        Returns:
            bool: True si debe incluir FID_ANTERIOR, False si no
        """
        if not datos_finales:
            return False
        
        # Verificar TIPO_PROYECTO en los datos
        for registro in datos_finales:
            tipo_proyecto = registro.get('TIPO_PROYECTO', '').strip().upper()
            
            # Si encuentra T1 o T3, debe incluir FID_ANTERIOR
            if tipo_proyecto in ['T1', 'T3']:
                return True
            # Si encuentra T2 o T4, no debe incluir FID_ANTERIOR
            elif tipo_proyecto in ['T2', 'T4']:
                return False
        
        # Por defecto, incluir FID_ANTERIOR si no se puede determinar
        return True
    
    def _preparar_datos_norma_finales(self, datos_norma):
        """Prepara los datos de norma aplicando transformaciones específicas"""
        datos_preparados = []
        
        for registro in datos_norma:
            registro_final = registro.copy()
            
            # 1. Corregir GRUPO para norma - debe ser "NODO ELECTRICO" para expansión
            # Con clasificación automática, verificamos el TIPO_PROYECTO del registro
            tipo_proyecto = registro_final.get('TIPO_PROYECTO', '')
            if 'EXPANSION' in str(tipo_proyecto).upper():
                registro_final['GRUPO'] = 'NODO ELECTRICO'
            
            # 2. Corregir TIPO_ADECUACION para quitar tildes
            tipo_adecuacion = registro_final.get('TIPO_ADECUACION', '')
            if tipo_adecuacion:
                conversiones_tipo_adecuacion = {
                    'RETENCIÓN': 'RETENCION',
                    'SUSPENSIÓN': 'SUSPENSION',
                    'retención': 'RETENCION',
                    'suspensión': 'SUSPENSION',
                    'Retención': 'RETENCION',
                    'Suspensión': 'SUSPENSION'
                }
                registro_final['TIPO_ADECUACION'] = conversiones_tipo_adecuacion.get(
                    tipo_adecuacion, tipo_adecuacion.upper()
                )
            
            # 3. Asegurar formato de fecha
            fecha = registro_final.get('FECHA_INSTALACION', '')
            if fecha:
                registro_final['FECHA_INSTALACION'] = self.clasificador._formatear_fecha(fecha)
            
            # 4. Limpiar campos que no deben ir en norma pero podrían estar presentes
            campos_norma_validos = [
                'ENLACE', 'NORMA', 'GRUPO', 'CIRCUITO', 'CODIGO_TRAFO',
                'CANTIDAD','MACRONORMA', 'FECHA_INSTALACION', 'TIPO_ADECUACION', 'OBSERVACIONES'
            ]
            
            # Solo mantener campos válidos para norma
            registro_norma_limpio = {}
            for campo in campos_norma_validos:
                registro_norma_limpio[campo] = registro_final.get(campo, '')
            
            datos_preparados.append(registro_norma_limpio)
        
        return datos_preparados

    def generar_norma_xml(self):
        """Genera archivo XML específico para la norma con estructura de configuración exacta"""
        try:
            from xml.etree.ElementTree import Element, SubElement, tostring
            from xml.dom import minidom
            
            filename = f"norma_{self.proceso.id}.xml"
            filepath = os.path.join(self.base_path, filename)
            
            # Crear estructura XML
            root = Element('Configuracion')
            
            # Agregar elementos básicos
            elemento = SubElement(root, 'Elemento')
            elemento.text = 'Poste'
            
            comp_repetitiva = SubElement(root, 'ComponenteRepetitiva')
            comp_repetitiva.text = 'Norma'
            
            # Crear sección de campos
            campos = SubElement(root, 'Campos')
            
            # Configuración de campos para norma - ORDEN Y CAMPOS EXACTOS SEGÚN ESPECIFICACIÓN
            campos_config = [
                {'nombre': 'NORMA', 'componente': 'NORMA', 'atributo': 'NORMA'},
                {'nombre': 'GRUPO', 'componente': 'NORMA', 'atributo': 'GRUPO'},
                {'nombre': 'CIRCUITO', 'componente': 'NORMA', 'atributo': 'CIRCUITO'},
                {'nombre': 'CODIGO_TRAFO', 'componente': 'NORMA', 'atributo': 'CODIGO_TRAFO'},
                {'nombre': 'CANTIDAD', 'componente': 'NORMA', 'atributo': 'CANTIDAD'},
                {'nombre': 'MACRONORMA', 'componente': 'NORMA', 'atributo': 'MACRONORMA'},
                {'nombre': 'FECHA_INSTALACION', 'componente': 'NORMA', 'atributo': 'FECHA_INSTALACION'},
                {'nombre': 'TIPO_ADECUACION', 'componente': 'NORMA', 'atributo': 'TIPO_ADECUACION'},
                {'nombre': 'OBSERVACIONES', 'componente': 'NORMA', 'atributo': 'OBSERVACIONES'},
            ]
            
            # Agregar cada campo
            for i, campo_config in enumerate(campos_config):
                campo_elem = SubElement(campos, f'Campo{i}')
                
                nombre = SubElement(campo_elem, 'Nombre')
                nombre.text = campo_config['nombre']
                
                componente = SubElement(campo_elem, 'Componente')
                componente.text = campo_config['componente']
                
                atributo = SubElement(campo_elem, 'Atributo')
                atributo.text = campo_config['atributo']
            
            # Formatear XML
            rough_string = tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")
            
            # Eliminar la declaración XML <?xml version="1.0" ?>
            lines = pretty_xml.split('\n')
            if lines[0].startswith('<?xml'):
                lines = lines[1:]  # Eliminar la primera línea con la declaración XML
            pretty_xml_sin_declaracion = '\n'.join(lines)
            
            # Escribir archivo
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(pretty_xml_sin_declaracion)
            
            return filename
            
        except Exception as e:
            raise Exception(f"Error generando archivo XML de norma: {str(e)}")
    
    def _get_tipo_campo_norma(self, campo):
        """Determina el tipo de dato para campos de norma en XML"""
        if campo in ['CANTIDAD']:
            return 'numero'
        elif campo in ['FECHA_INSTALACION']:
            return 'fecha'
        else:
            return 'texto'

    def generar_xml(self):
        """Genera archivo XML con la estructura específica requerida para el sistema"""
        try:
            from xml.etree.ElementTree import Element, SubElement, tostring
            from xml.dom import minidom
            
            filename = f"estructuras_{self.proceso.id}.xml"
            filepath = os.path.join(self.base_path, filename)
            
            # Crear estructura XML según especificación
            root = Element('Configuracion')
            
            # Elemento principal
            elemento = SubElement(root, 'Elemento')
            elemento.text = 'Poste'
            
            # Contenedor de campos
            campos = SubElement(root, 'Campos')
            
            # Definición de campos EXACTA según tu XML funcional
            campos_config = [
                {'nombre': 'GRUPO', 'componente': 'EPOSTE_AT', 'atributo': 'GRUPO'},
                {'nombre': 'TIPO', 'componente': 'EPOSTE_AT', 'atributo': 'TIPO'},
                {'nombre': 'CLASE', 'componente': 'EPOSTE_AT', 'atributo': 'CLASE'},
                {'nombre': 'USO', 'componente': 'EPOSTE_AT', 'atributo': 'USO'},
                {'nombre': 'ESTADO', 'componente': 'CCOMUN', 'atributo': 'ESTADO'},
                {'nombre': 'TIPO_ADECUACION', 'componente': 'EPOSTE_AT', 'atributo': 'TIPO_ADECUACION'},
                {'nombre': 'PROPIETARIO', 'componente': 'CPROPIETARIO', 'atributo': 'PROPIETARIO_1'},
                {'nombre': 'PORCENTAJE_PROPIEDAD', 'componente': 'CPROPIETARIO', 'atributo': 'PORCENTAJE_PROP_1'},
                {'nombre': 'UBICACION', 'componente': 'CCOMUN', 'atributo': 'UBICACION'},
                {'nombre': 'CODIGO_MATERIAL', 'componente': 'CCOMUN', 'atributo': 'CODIGO_MATERIAL'},
                {'nombre': 'FECHA_INSTALACION', 'componente': 'CCOMUN', 'atributo': 'FECHA_INSTALACION'},
                {'nombre': 'FECHA_OPERACION', 'componente': 'CCOMUN', 'atributo': 'FECHA_OPERACION'},
                {'nombre': 'PROYECTO', 'componente': 'CCOMUN', 'atributo': 'PROYECTO'},
                {'nombre': 'EMPRESA', 'componente': 'CCOMUN', 'atributo': 'EMPRESA_ORIGEN'},
                {'nombre': 'OBSERVACIONES', 'componente': 'CCOMUN', 'atributo': 'OBSERVACIONES'},
                {'nombre': 'CLASIFICACION_MERCADO', 'componente': 'CCOMUN', 'atributo': 'CLASIFICACION_MERCADO'},
                {'nombre': 'TIPO_PROYECTO', 'componente': 'CCOMUN', 'atributo': 'TIPO_PROYECTO'},
                {'nombre': 'ID_MERCADO', 'componente': 'CCOMUN', 'atributo': 'ID_MERCADO'},
                {'nombre': 'UC', 'componente': 'CCOMUN', 'atributo': 'UC'},
                {'nombre': 'ESTADO_SALUD', 'componente': 'CCOMUN', 'atributo': 'ESTADO_SALUD'},
                {'nombre': 'OT_MAXIMO', 'componente': 'CCOMUN', 'atributo': 'OT_MAXIMO'},
                {'nombre': 'CODIGO_MARCACION', 'componente': 'CCOMUN', 'atributo': 'CODIGO_MARCACION'},
                {'nombre': 'SALINIDAD', 'componente': 'CCOMUN', 'atributo': 'SALINIDAD'},
                {'nombre': 'G3E_GEOMETRY', 'componente': '', 'atributo': ''},
            ]

            # Agregar cada campo con su número correcto
            for i, campo_config in enumerate(campos_config):
                campo_elem = SubElement(campos, f'Campo{i}')

                nombre = SubElement(campo_elem, 'Nombre')
                nombre.text = campo_config['nombre']

                componente = SubElement(campo_elem, 'Componente')
                componente.text = campo_config['componente']

                atributo = SubElement(campo_elem, 'Atributo')
                atributo.text = campo_config['atributo']

            # Formatear XML con indentación bonita
            rough_string = tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")

            # Eliminar la declaración XML <?xml version="1.0" ?>
            lines = pretty_xml.split('\n')
            if lines[0].startswith('<?xml'):
                lines = lines[1:]
            while lines and lines[-1].strip() == '':
                lines.pop()

            pretty_xml_sin_declaracion = '\n'.join(lines)

            # Escribir archivo
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(pretty_xml_sin_declaracion)

            return filename

        except Exception as e:
            raise Exception(f"Error generando archivo XML: {str(e)}")

class ClasificadorEstructuras:
    """Aplica las reglas de clasificación de estructuras según las reglas de negocio"""
    
    def __init__(self):
        pass
    
    def clasificar_estructura(self, registro: Dict) -> Dict:
        """
        Aplica las reglas de clasificación a un registro
        
        Reglas de negocio:
        1. GRUPO siempre debe ser "ESTRUCTURAS EYT" (para todas las estructuras)
        2. CLASE siempre debe ser "POSTE" (para todas las estructuras)
        3. USO siempre debe ser "DISTRIBUCION ENERGIA" (para todas las estructuras)
        4. TIPO se determina únicamente por la Unidad Constructiva (UC):
           - Si UC empieza con N1 -> TIPO = "SECUNDARIO"
           - Si UC empieza con N2, N3, N4 -> TIPO = "PRIMARIO"
           - Valor por defecto: "SECUNDARIO"
        5. TIPO_PROYECTO: convertir números romanos (I, II, III, IV) a formato T+número (T1, T2, T3, T4)
        """
        registro_clasificado = registro.copy()
        
        # Inicializar lista de observaciones
        observaciones_clasificacion = []
        
        # Regla 1: GRUPO siempre debe ser "ESTRUCTURAS EYT" (para todas las estructuras)
        registro_clasificado['GRUPO'] = 'ESTRUCTURAS EYT'
        
        # Regla 2: CLASE siempre debe ser "POSTE" (para todas las estructuras)
        registro_clasificado['CLASE'] = 'POSTE'
        
        # Regla 3: USO siempre debe ser "DISTRIBUCION ENERGIA" (para todas las estructuras)
        registro_clasificado['USO'] = 'DISTRIBUCION ENERGIA'
        
        # Regla 3b: PORCENTAJE_PROPIEDAD siempre debe ser "100" (para todas las estructuras)
        registro_clasificado['PORCENTAJE_PROPIEDAD'] = '100'
        
        # Para PROPIETARIO: clasificar el nombre del Excel a una categoría predefinida
        propietario_nombre = registro.get('PROPIETARIO', '')
        propietario_clasificado = self._clasificar_propietario(propietario_nombre)
        registro_clasificado['PROPIETARIO'] = propietario_clasificado
        
        # Regla 4: Clasificar TIPO basado únicamente en Unidad Constructiva (UC)
        uc = registro.get('UC', '').strip().upper()
        tipo_clasificado = self._clasificar_tipo_por_uc(uc)
        registro_clasificado['TIPO'] = tipo_clasificado
        
        # Regla 5: Generar TIPO_PROYECTO basado en NIVEL_TENSION o UC
        nivel_tension = registro.get('NIVEL_TENSION', '').strip()
        uc = registro.get('UC', '').strip()
        
        # Usar NIVEL_TENSION primero, si no está disponible usar UC
        valor_para_mapeo = nivel_tension if nivel_tension else uc
        
        tipo_proyecto_generado = self._generar_tipo_proyecto_desde_nivel_tension(valor_para_mapeo)
        if tipo_proyecto_generado:
            registro_clasificado['TIPO_PROYECTO'] = tipo_proyecto_generado
            observaciones_clasificacion.append(f"TIPO_PROYECTO generado como '{tipo_proyecto_generado}' basado en {'NIVEL_TENSION' if nivel_tension else 'UC'}: {valor_para_mapeo}")
        else:
            # Fallback: Convertir TIPO_PROYECTO de números romanos a formato T+número si existe
            tipo_proyecto_original = registro.get('TIPO_PROYECTO', '').strip()
            tipo_proyecto_convertido = self._convertir_tipo_proyecto(tipo_proyecto_original)
            registro_clasificado['TIPO_PROYECTO'] = tipo_proyecto_convertido
        
        # Regla 6: FECHA_OPERACION debe ser igual a FECHA_INSTALACION (solo fecha, sin hora)
        fecha_instalacion = registro.get('FECHA_INSTALACION', '')
        if fecha_instalacion:
            # Formatear fecha para mostrar solo fecha sin hora
            fecha_formateada = self._formatear_fecha(fecha_instalacion)
            registro_clasificado['FECHA_INSTALACION'] = fecha_formateada
            registro_clasificado['FECHA_OPERACION'] = fecha_formateada
        
        # Regla 7: Asignar CODIGO_MATERIAL basado en UC
        codigo_material = self._asignar_codigo_material(uc)
        if codigo_material:
            registro_clasificado['CODIGO_MATERIAL'] = codigo_material
        
        # Regla 8: Convertir ESTADO_SALUD de números a descriptivos
        estado_salud_convertido = self._convertir_estado_salud(registro.get('ESTADO_SALUD', ''))
        if estado_salud_convertido:
            registro_clasificado['ESTADO_SALUD'] = estado_salud_convertido
        
        # Agregar observaciones de clasificación (solo si no hay observaciones del Excel original)
        observaciones_clasificacion.append(f"TIPO clasificado como {tipo_clasificado} basado en UC: {uc}")
        observaciones_clasificacion.append("GRUPO forzado a 'ESTRUCTURAS EYT'")
        observaciones_clasificacion.append("CLASE forzada a 'POSTE'")
        observaciones_clasificacion.append("USO forzado a 'DISTRIBUCION ENERGIA'")
        observaciones_clasificacion.append("PORCENTAJE_PROPIEDAD forzado a '100'")
        if codigo_material:
            observaciones_clasificacion.append(f"CODIGO_MATERIAL asignado como '{codigo_material}' basado en UC: {uc}")
        if estado_salud_convertido and estado_salud_convertido != registro.get('ESTADO_SALUD', ''):
            observaciones_clasificacion.append(f"ESTADO_SALUD convertido de '{registro.get('ESTADO_SALUD', '')}' a '{estado_salud_convertido}'")
        if tipo_proyecto_generado:
            observaciones_clasificacion.append(f"TIPO_PROYECTO generado como '{tipo_proyecto_generado}' basado en {'NIVEL_TENSION' if nivel_tension else 'UC'}: {valor_para_mapeo}")
        elif tipo_proyecto_original != tipo_proyecto_convertido:
            observaciones_clasificacion.append(f"TIPO_PROYECTO convertido de '{tipo_proyecto_original}' a '{tipo_proyecto_convertido}'")
        if fecha_instalacion:
            observaciones_clasificacion.append("FECHA_OPERACION igualada a FECHA_INSTALACION")
        
        # Solo agregar observaciones de clasificación si no hay observaciones del Excel original
        if not registro.get('OBSERVACIONES', '').strip():
            # Si no hay observaciones del Excel, dejar el campo vacío (no agregar observaciones de clasificación)
            registro_clasificado['OBSERVACIONES'] = ''
        # Si ya hay observaciones del Excel original, mantenerlas sin agregar observaciones de clasificación
        
        # Guardar observaciones de clasificación en un campo separado para debugging/auditoría
        registro_clasificado['OBSERVACION_CLASIFICACION_SISTEMA'] = "; ".join(observaciones_clasificacion)
        
        # Agregar metadatos de clasificación
        registro_clasificado['FECHA_CLASIFICACION'] = datetime.now().isoformat()
        registro_clasificado['VERSION_REGLAS'] = '2.5'
        
        return registro_clasificado
    
    def _convertir_tipo_proyecto(self, tipo_proyecto: str) -> str:
        """
        Convierte números romanos a formato T+número para TIPO_PROYECTO
        
        I -> T1, II -> T2, III -> T3, IV -> T4
        """
        if not tipo_proyecto:
            return tipo_proyecto
        
        tipo_limpio = tipo_proyecto.strip().upper()
        conversion_map = REGLAS_CLASIFICACION['CONVERSION_TIPO_PROYECTO']
        
        return conversion_map.get(tipo_limpio, tipo_proyecto)  # Si no coincide, mantener valor original
    
    def _generar_tipo_proyecto_desde_nivel_tension(self, nivel_tension: str) -> str:
        """
        Genera TIPO_PROYECTO basado en NIVEL_TENSION
        
        N3L75 -> T1, N3L79 -> T3, etc.
        """
        if not nivel_tension:
            return REGLAS_CLASIFICACION['CONVERSION_TIPO_PROYECTO']['VALOR_DEFECTO']
        
        nivel_limpio = nivel_tension.strip().upper()
        mapeo_nivel = REGLAS_CLASIFICACION['CONVERSION_TIPO_PROYECTO']['MAPEO_NIVEL_TENSION']
        
        # Buscar coincidencia exacta primero
        if nivel_limpio in mapeo_nivel:
            return mapeo_nivel[nivel_limpio]
        
        # Buscar coincidencia por patrón (ej: N1L, N2L, N3L, N4L)
        for patron, tipo_proyecto in mapeo_nivel.items():
            if patron.endswith('L') and nivel_limpio.startswith(patron):
                return tipo_proyecto
        
        return REGLAS_CLASIFICACION['CONVERSION_TIPO_PROYECTO']['VALOR_DEFECTO']  # No se encontró mapeo
    
    def _clasificar_propietario(self, nombre_propietario: str) -> str:
        """
        Clasifica el nombre del propietario del Excel a una categoría predefinida
        
        Args:
            nombre_propietario: Nombre del propietario tal como viene en el Excel
            
        Returns:
            Categoría del propietario: 'CENS', 'PARTICULAR', 'ESTADO', o 'COMPARTIDO'
        """
        if not nombre_propietario:
            return 'PARTICULAR'  # Valor por defecto
        
        nombre_limpio = nombre_propietario.strip().upper()
        
        # Reglas de clasificación basadas en el nombre del propietario
        if any(keyword in nombre_limpio for keyword in ['CENS', 'CENTRALES', 'ELECTRICA']):
            return 'CENS'
        elif any(keyword in nombre_limpio for keyword in ['ESTADO', 'GOBIERNO', 'PUBLICO', 'MINISTERIO']):
            return 'ESTADO'
        elif any(keyword in nombre_limpio for keyword in ['COMPARTIDO', 'CONSORCIO', 'SOCIEDAD']):
            return 'COMPARTIDO'
        else:
            # Por defecto, clasificar como PARTICULAR para nombres de empresas privadas
            return 'PARTICULAR'
    
    def _formatear_fecha(self, fecha) -> str:
        """
        Formatea una fecha para mostrar solo la fecha sin la hora en formato DD/MM/YYYY
        """
        return DataUtils.formatear_fecha(fecha)
    
    def verificar_propietarios_en_excel(self, registros: List[Dict]) -> Dict:
        """
        Verifica si hay propietarios definidos en el Excel
        
        Returns:
            Dict con información sobre propietarios encontrados
        """
        propietarios_encontrados = set()
        registros_con_propietario = 0
        registros_sin_propietario = 0
        
        for registro in registros:
            propietario = registro.get('PROPIETARIO', '')
            # Convertir a string y limpiar espacios, manejar valores no string
            if propietario is not None:
                propietario = str(propietario).strip()
            else:
                propietario = ''
                
            if propietario:
                propietarios_encontrados.add(propietario)
                registros_con_propietario += 1
            else:
                registros_sin_propietario += 1
        
        return {
            'tiene_propietarios': len(propietarios_encontrados) > 0,
            'propietarios_unicos': list(propietarios_encontrados),
            'registros_con_propietario': registros_con_propietario,
            'registros_sin_propietario': registros_sin_propietario,
            'total_registros': len(registros),
            'propietario_unico': list(propietarios_encontrados)[0] if len(propietarios_encontrados) == 1 else None
        }
    
    def aplicar_propietario_a_todos(self, registros: List[Dict], propietario: str) -> List[Dict]:
        """
        Aplica el mismo propietario a todos los registros
        
        Args:
            registros: Lista de registros a actualizar
            propietario: Propietario a aplicar (debe ser uno de los predefinidos)
        
        Returns:
            Lista de registros actualizados
        """
        propietarios_validos = REGLAS_CLASIFICACION['PROPIETARIOS_VALIDOS']['VALORES_ACEPTADOS']
        
        if propietario not in propietarios_validos:
            raise ValueError(f"Propietario '{propietario}' no es válido. Debe ser uno de: {propietarios_validos}")
        
        registros_actualizados = []
        for registro in registros:
            registro_actualizado = registro.copy()
            registro_actualizado['PROPIETARIO'] = propietario
            # PORCENTAJE_PROPIEDAD ya se aplica en clasificar_estructura
            registros_actualizados.append(registro_actualizado)
        
        return registros_actualizados
    
    def aplicar_propietario_a_proceso(self, proceso, propietario: str) -> None:
        """
        Aplica el propietario seleccionado a todos los registros del proceso
        
        Args:
            proceso: Instancia del modelo ProcesoEstructura
            propietario: Propietario a aplicar (debe ser uno de los predefinidos)
        """
        propietarios_validos = REGLAS_CLASIFICACION['PROPIETARIOS_VALIDOS']['VALORES_ACEPTADOS']
        
        if propietario not in propietarios_validos:
            raise ValueError(f"Propietario '{propietario}' no es válido. Debe ser uno de: {propietarios_validos}")
        
        # Aplicar propietario a todos los registros de datos_norma
        if proceso.datos_norma:
            datos_actualizados = []
            for registro in proceso.datos_norma:
                registro_actualizado = registro.copy()
                registro_actualizado['PROPIETARIO'] = propietario
                registro_actualizado['PORCENTAJE_PROPIEDAD'] = '100'
                datos_actualizados.append(registro_actualizado)
            
            proceso.datos_norma = datos_actualizados
            print(f"Propietario '{propietario}' aplicado a {len(datos_actualizados)} registros")
        else:
            print("No hay datos_norma para actualizar")
        
        # Marcar que el propietario ya fue definido y guardar el valor
        proceso.propietario_definido = propietario  # Guardar el propietario seleccionado
        proceso.requiere_definir_propietario = False  # Ya no se requiere definir propietario
        proceso.save()
        print(f"Proceso actualizado: propietario_definido='{proceso.propietario_definido}', requiere_definir_propietario={proceso.requiere_definir_propietario}")
    
    def verificar_y_marcar_campos_requeridos(self, proceso) -> Dict:
        """
        Verifica qué campos requieren ser completados por el usuario
        y marca el proceso accordingly.
        
        Returns:
            Dict con información sobre campos que requieren completarse
        """
        campos_requeridos = {
            'propietario': False,
            'estado_salud': False,
            'detalles': {}
        }
        
        # Verificar PROPIETARIO
        if not proceso.propietario_definido:
            campos_requeridos['propietario'] = True
            proceso.requiere_definir_propietario = True
        
        # Verificar ESTADO_SALUD
        estado_salud_vacio = False
        if proceso.datos_excel:
            for registro in proceso.datos_excel:
                if not registro.get('ESTADO_SALUD') or registro.get('ESTADO_SALUD').strip() == '':
                    estado_salud_vacio = True
                    break
        
        if estado_salud_vacio and not (proceso.estado_salud_definido and proceso.estado_salud_definido != 'None'):
            campos_requeridos['estado_salud'] = True
            campos_requeridos['detalles']['estado_salud'] = 'ESTADO_SALUD está vacío en los datos del Excel'
        
        # Guardar cambios si es necesario
        proceso.save()
        
        return campos_requeridos
    
    def _clasificar_tipo_por_uc(self, uc: str) -> str:
        """
        Clasifica el TIPO basado en la Unidad Constructiva (UC)
        
        Lógica:
        - N1 -> SECUNDARIO
        - N2, N3, N4 -> PRIMARIO
        - Valor por defecto: SECUNDARIO
        """
        if not uc:
            return REGLAS_CLASIFICACION['CLASIFICACION_TIPO_POR_UC']['VALOR_DEFECTO']
        
        # Buscar patrones en las reglas
        for regla in REGLAS_CLASIFICACION['CLASIFICACION_TIPO_POR_UC']['REGLAS_PRIORITARIAS']:
            patron = regla['PATRON']
            if re.match(patron, uc):
                return regla['TIPO']
        
        # Si no coincide con ningún patrón, usar valor por defecto
        return REGLAS_CLASIFICACION['CLASIFICACION_TIPO_POR_UC']['VALOR_DEFECTO']
    
    def clasificar_lote(self, registros: List[Dict]) -> List[Dict]:
        """Aplica clasificación a un lote de registros"""
        registros_clasificados = []
        estadisticas = {
            'total_procesados': len(registros),
            'clasificados_como_poste': 0,
            'estructuras_eyt': 0
        }
        
        for registro in registros:
            registro_clasificado = self.clasificar_estructura(registro)
            registros_clasificados.append(registro_clasificado)
            
            # Estadísticas
            if registro_clasificado.get('TIPO_CLASIFICADO') == 'POSTE':
                estadisticas['clasificados_como_poste'] += 1
            if registro_clasificado.get('CATEGORIA_ESTRUCTURA') == 'ESTRUCTURAS EYT':
                estadisticas['estructuras_eyt'] += 1
        
        return registros_clasificados, estadisticas
    
    def obtener_estadisticas(self, registros: List[Dict]) -> Dict:
        """Genera estadísticas de clasificación para la UI"""
        estadisticas = {
            'total_registros': len(registros),
            'por_tipo_estructura': {},
            'clasificaciones_aplicadas': []
        }
        
        # Contar por tipo de estructura actual
        tipos_contador = {}
        grupos_contador = {}
        clasificaciones_tipo = {}
        
        for registro in registros:
            # Contar tipos actuales
            tipo_actual = registro.get('TIPO', 'SIN_TIPO')
            tipos_contador[tipo_actual] = tipos_contador.get(tipo_actual, 0) + 1
            
            # Contar grupos actuales
            grupo_actual = registro.get('GRUPO', 'SIN_GRUPO')
            grupos_contador[grupo_actual] = grupos_contador.get(grupo_actual, 0) + 1
            
            # Verificar si hubo cambio de TIPO por regla de clasificación
            if registro.get('OBSERVACION_CLASIFICACION'):
                clasificaciones_tipo['GRUPO_to_POSTE'] = clasificaciones_tipo.get('GRUPO_to_POSTE', 0) + 1
        
        estadisticas['por_tipo_estructura'] = tipos_contador
        estadisticas['por_grupo_estructura'] = grupos_contador
        
        # Convertir clasificaciones a formato para UI
        for key, cantidad in clasificaciones_tipo.items():
            if key == 'GRUPO_to_POSTE':
                estadisticas['clasificaciones_aplicadas'].append({
                    'tipo_original': 'Estructura con GRUPO',
                    'tipo_nuevo': 'POSTE',
                    'cantidad': cantidad
                })
        
        # Agregar estadística fija para GRUPO -> ESTRUCTURAS EYT
        if grupos_contador.get('ESTRUCTURAS EYT', 0) > 0:
            estadisticas['clasificaciones_aplicadas'].append({
                'tipo_original': 'Todas las estructuras',
                'tipo_nuevo': 'ESTRUCTURAS EYT',
                'cantidad': grupos_contador.get('ESTRUCTURAS EYT', 0)
            })
        
        return estadisticas
    
    def obtener_resumen_clasificacion(self, registros: List[Dict]) -> Dict:
        """Genera un resumen de la clasificación aplicada"""
        resumen = {
            'total_registros': len(registros),
            'tipos_encontrados': {},
            'grupos_encontrados': {},
            'clasificaciones_aplicadas': {}
        }
        
        for registro in registros:
            # Contar tipos originales
            tipo_original = registro.get('TIPO', 'SIN_TIPO')
            resumen['tipos_encontrados'][tipo_original] = resumen['tipos_encontrados'].get(tipo_original, 0) + 1
            
            # Contar grupos
            grupo = registro.get('GRUPO', 'SIN_GRUPO')
            resumen['grupos_encontrados'][grupo] = resumen['grupos_encontrados'].get(grupo, 0) + 1
            
            # Contar clasificaciones aplicadas
            clasificacion = registro.get('TIPO_CLASIFICADO', 'SIN_CLASIFICACION')
            resumen['clasificaciones_aplicadas'][clasificacion] = resumen['clasificaciones_aplicadas'].get(clasificacion, 0) + 1
        
        return resumen
    
    def _asignar_codigo_material(self, uc: str) -> str:
        """
        Asigna CODIGO_MATERIAL basado en el UC (Unidad Constructiva) usando mapeo jerárquico
        
        Sistema de mapeo jerárquico:
        1. Mapeos directos específicos (para UCs conocidos)
        2. Mapeo por patrones regex (extrae altura y carga)
        3. Mapeo por defecto basado en tipo de estructura
        
        Args:
            uc: Unidad Constructiva (ej: N3L75, N2L79, etc.)
            
        Returns:
            Código de material del catálogo o cadena vacía si no se encuentra
        """
        
        if not uc or uc is None:
            return ''
        
        uc_limpio = str(uc).strip().upper()
        
        if not uc_limpio:
            return ''
        
        # 1. Buscar en mapeos directos específicos
        mapeos_directos = MAPEO_UC_MATERIAL.get('MAPEOS_DIRECTOS', {})
        if uc_limpio in mapeos_directos:
            codigo_directo = mapeos_directos[uc_limpio]
            if codigo_directo in CATALOGO_MATERIALES:
                return codigo_directo
        
        # 2. Buscar por patrones regex
        reglas_patron = MAPEO_UC_MATERIAL.get('REGLAS_POR_PATRON', [])
        for regla in reglas_patron:
            patron = regla.get('patron', '')
            if not patron:
                continue
                
            match = re.match(patron, uc_limpio)
            if match:
                # Para patron N[nivel]L[carga]
                if 'mapeo' in regla:
                    carga = match.group(1)
                    mapeo_cargas = regla['mapeo']
                    if carga in mapeo_cargas:
                        codigo_patron = mapeo_cargas[carga]
                        if codigo_patron in CATALOGO_MATERIALES:
                            return codigo_patron
                
                # Para patron con altura explícita
                if 'alturas' in regla:
                    altura = match.group(1)
                    mapeo_alturas = regla['alturas']
                    if altura in mapeo_alturas:
                        # Tomar el primer código disponible para esa altura
                        codigos_altura = mapeo_alturas[altura]
                        for codigo_altura in codigos_altura:
                            if codigo_altura in CATALOGO_MATERIALES:
                                return codigo_altura
        
        # 3. Mapeo por defecto basado en clasificación de tipo
        tipo_estructura = self._clasificar_tipo_por_uc(uc_limpio)
        mapeo_defecto = MAPEO_UC_MATERIAL.get('MAPEO_POR_DEFECTO', {})
        
        if tipo_estructura in mapeo_defecto:
            codigo_defecto = mapeo_defecto[tipo_estructura]
            if codigo_defecto in CATALOGO_MATERIALES:
                return codigo_defecto
        
        # 4. Si no se encuentra nada, devolver cadena vacía
        return ''
    
    def _convertir_estado_salud(self, estado_salud) -> str:
        """
        Convierte valores de estado de salud de números a descriptivos
        
        Conversiones:
        1 -> BUENO
        2 -> REGULAR  
        3 -> MALO
        
        Solo se permiten los estados: BUENO, REGULAR, MALO
        También maneja valores ya descriptivos y devuelve cadena vacía
        para valores no reconocidos o nulos.
        """
        
        if not estado_salud or str(estado_salud).strip().upper() in ['', 'NAN', 'NONE']:
            return ''
        
        estado_str = str(estado_salud).strip().upper()
        
        # Buscar en el mapeo de estados
        estado_convertido = ESTADOS_SALUD.get(estado_str, '')
        
        # Solo permitir estados válidos: BUENO, REGULAR, MALO
        if estado_convertido in ['BUENO', 'REGULAR', 'MALO']:
            return estado_convertido
        
        # Si el valor no es válido, retornar vacío para que el usuario lo complete
        return ''
