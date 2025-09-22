# SISTEMA DE CLASIFICACIÓN AUTOMÁTICA DE ESTRUCTURAS ELÉCTRICAS
# Archivo de configuración central para reglas de negocio y mapeos de datos
# Última actualización: 2025-08-29
# Fuente: Sistema Transformador - CENS

# =============================================================================
# SECCIÓN 1: REGLAS DE CLASIFICACIÓN Y VALIDACIÓN
# =============================================================================

# Reglas principales de clasificación automática de estructuras
REGLAS_CLASIFICACION = {
    # Valores constantes que se aplican a TODAS las estructuras (sin excepción)
    'VALORES_UNIVERSALES': {
        'ESTRUCTURA': 'ESTRUCTURAS EYT',     # Tipo de infraestructura fija
        'CLASE': 'POSTE',                   # Categoría técnica estándar
        'USO': 'DISTRIBUCION ENERGIA',      # Propósito operacional
        'PORCENTAJE_PROPIEDAD': '100',      # Propiedad completa de CENS
        'ID_MERCADO': '161',                # Identificador regulatorio único
        'SALINIDAD': 'NO',                  # Condición ambiental por defecto (excepto costa)
    },
    
    # Clasificación automática por campo GRUPO (regla prioritaria)
    'CLASIFICACION_POR_GRUPO': {
        'CAMPO_ORIGEN': 'GRUPO',
        'VALOR_DESTINO': 'POSTE',
        'CONDICION': 'Si GRUPO tiene valor, siempre clasifica como POSTE'
    },
    
    # Catálogo de propietarios válidos con reglas de normalización
    'PROPIETARIOS_VALIDOS': {
        'VALORES_ACEPTADOS': ['CENS', 'PARTICULAR', 'ESTADO', 'COMPARTIDO'],
        'NORMALIZACION': {
            'CENS SA ESP': 'CENS',
            'CENTRALES ELECTRICAS': 'CENS', 
            'PRIVADO': 'PARTICULAR',
            'PUBLICO': 'ESTADO',
            'MIXTO': 'COMPARTIDO'
        },
        'VALOR_DEFECTO': 'CENS'  # Si no se puede determinar
    },
    
    # Estados operacionales con validaciones temporales
    'ESTADOS_OPERACIONALES': {
        'VALORES_VALIDOS': ['CONSTRUCCION', 'RETIRADO', 'OPERACION'],
        'VALIDACIONES_TEMPORALES': {
            'CONSTRUCCION': 'Requiere FECHA_INSTALACION futura o reciente',
            'OPERACION': 'Requiere FECHA_OPERACION <= fecha actual',
            'RETIRADO': 'Requiere FECHA_FUERA_OPERACION'
        },
        'TRANSICIONES_VALIDAS': {
            'CONSTRUCCION': ['OPERACION', 'RETIRADO'],
            'OPERACION': ['RETIRADO'],
            'RETIRADO': []  # Estado final
        },
        'VALOR_DEFECTO': 'OPERACION'
    },
    
    # Conversión inteligente de tipos de proyecto (con validaciones)
    'CONVERSION_TIPO_PROYECTO': {
        'PATRONES_ROMANOS': {
            'I': 'T1', 'II': 'T2', 'III': 'T3', 'IV': 'T4',
            '1': 'T1', '2': 'T2', '3': 'T3', '4': 'T4'  # Soporte numérico
        },
        'MAPEO_NIVEL_TENSION': {
            'N1L': 'T1', 'N2L': 'T2', 'N3L': 'T3', 'N4L': 'T4',
            'N1': 'T1', 'N2': 'T2', 'N3': 'T3', 'N4': 'T4'  # Sin L también válido
        },
        'VALOR_DEFECTO': 'T1'  # Cuando no se puede determinar
    },
    
    # Clasificación automática de TIPO basada en UC (con reglas jerárquicas)
    'CLASIFICACION_TIPO_POR_UC': {
        'REGLAS_PRIORITARIAS': [
            {'PATRON': r'^N1', 'TIPO': 'SECUNDARIO', 'DESCRIPCION': 'Nivel 1 = Baja tensión'},
            {'PATRON': r'^N[234]', 'TIPO': 'PRIMARIO', 'DESCRIPCION': 'Niveles 2-4 = Media/Alta tensión'}
        ],
        'VALIDACIONES_CRUZADAS': {
            'SECUNDARIO': {'NIVEL_TENSION_ESPERADO': 'N1L', 'TIPO_PROYECTO_ESPERADO': 'T1'},
            'PRIMARIO': {'NIVEL_TENSION_ESPERADO': ['N2L', 'N3L', 'N4L'], 'TIPO_PROYECTO_ESPERADO': ['T2', 'T3', 'T4']}
        },
        'VALOR_DEFECTO': 'PRIMARIO'  # Mayoría son primarios
    }
}

# =============================================================================
# SECCIÓN 2: CONFIGURACIÓN DE CAMPOS POR TIPO DE ESTRUCTURA  
# =============================================================================

# Configuración detallada de campos y validaciones por tipo de estructura
# Incluye campos de entrada, salida, validaciones y transformaciones específicas
ESTRUCTURAS_CAMPOS = {
    'EXPANSION': {
        'METADATOS': {
            'descripcion': 'Nuevas estructuras para ampliación de red',
            'prioridad_campos': ['COORDENADA_X', 'COORDENADA_Y', 'UC', 'NIVEL_TENSION'],
            'validaciones_especiales': ['coordenadas_en_area_concesion', 'uc_nivel_coherente']
        },
        'ARCHIVOS_FUENTE': {
            'hoja_datos': 'Estructuras_N1-N2-N3',
            'hoja_norma': 'Norma de Expansion'
        },
        'CAMPOS_ENTRADA_OBLIGATORIOS': [
            'Coordenada_X1\nLONGITUD', 'Coordenada_Y1\nLATITUD', 
            'Apoyo', 'Tipo', 'Poblacion'
        ],
        'CAMPOS_SALIDA_DATOS': [
            'COORDENADA_X', 'COORDENADA_Y', 'GRUPO', 'TIPO', 'CLASE', 'USO', 
            'ESTADO', 'TIPO_ADECUACION', 'PROPIETARIO', 'PORCENTAJE_PROPIEDAD',
            'UBICACION', 'CODIGO_MATERIAL', 'FECHA_INSTALACION', 'FECHA_OPERACION',
            'PROYECTO', 'EMPRESA', 'OBSERVACIONES', 'CLASIFICACION_MERCADO',
            'TIPO_PROYECTO', 'ID_MERCADO', 'UC', 'NIVEL_TENSION', 'ESTADO_SALUD', 
            'OT_MAXIMO', 'CODIGO_MARCACION', 'SALINIDAD', 'FID_ANTERIOR', 'ENLACE'
        ],
        'CAMPOS_SALIDA_NORMA': [
            'ENLACE', 'NORMA', 'GRUPO', 'CIRCUITO', 'CODIGO_TRAFO',
            'CANTIDAD', 'MACRONORMA', 'FECHA_INSTALACION', 'TIPO_ADECUACION'
        ]
    },
    
    'REPOSICION_NUEVO': {
        'METADATOS': {
            'descripcion': 'Reemplazo de estructuras existentes por nuevas',
            'prioridad_campos': ['CODIGO_OPERATIVO', 'COORDENADA_X', 'COORDENADA_Y', 'UC'],
            'validaciones_especiales': ['codigo_operativo_existe', 'coordenadas_coherentes_con_existente']
        },
        'ARCHIVOS_FUENTE': {
            'hoja_datos': 'Estructuras_N1-N2-N3',
            'hoja_norma': 'Norma de Reposicion'
        },
        'CAMPOS_ENTRADA_OBLIGATORIOS': [
            'Código FID\nGIT', 'Coordenada_X1\nLONGITUD', 'Coordenada_Y1\nLATITUD'
        ],
        'CAMPOS_SALIDA_DATOS': [
            'CODIGO_OPERATIVO', 'COORDENADA_X', 'COORDENADA_Y', 'GRUPO', 'TIPO',
            'CLASE', 'USO', 'ESTADO', 'TIPO_ADECUACION', 'PROPIETARIO',
            'PORCENTAJE_PROPIEDAD', 'UBICACION', 'CODIGO_MATERIAL',
            'FECHA_INSTALACION', 'FECHA_OPERACION', 'PROYECTO', 'EMPRESA',
            'OBSERVACIONES', 'CLASIFICACION_MERCADO', 'TIPO_PROYECTO', 'ID_MERCADO',
            'UC', 'ESTADO_SALUD', 'OT_MAXIMO', 'CODIGO_MARCACION', 'SALINIDAD',
            'FID_ANTERIOR', 'ENLACE'
        ],
        'CAMPOS_SALIDA_NORMA': [
            'ENLACE', 'NORMA', 'CIRCUITO', 'CODIGO_TRAFO',
            'CANTIDAD', 'FECHA_INSTALACION', 'TIPO_ADECUACION'
        ]
    },
    
    'REPOSICION_BAJO': {
        'METADATOS': {
            'descripcion': 'Retiro de estructuras existentes (baja de inventario)',
            'prioridad_campos': ['G3E_FID', 'FECHA_INSTALACION', 'FECHA_FUERA_OPERACION'],
            'validaciones_especiales': ['fecha_fuera_operacion_posterior', 'codigo_fid_valido']
        },
        'ARCHIVOS_FUENTE': {
            'hoja_datos': 'Estructuras_N1-N2-N3',
            'hoja_norma': 'Norma de Reposicion'
        },
        'CAMPOS_ENTRADA_OBLIGATORIOS': [
            'Código FID\nGIT', 'Fecha Instalacion\nDD/MM/YYYY'
        ],
        'CAMPOS_SALIDA_DATOS': [
            'G3E_FID', 'FECHA_INSTALACION', 'FECHA_FUERA_OPERACION',
            'CODIGO_MATERIAL', 'TIPO_DISPOSICION', 'UC', 'NORMA', 'OBSERVACIONES'
        ],
        'CAMPOS_SALIDA_NORMA': [
            'ENLACE', 'NORMA', 'CIRCUITO', 'CODIGO_TRAFO',
            'CANTIDAD', 'FECHA_INSTALACION', 'TIPO_ADECUACION'
        ]
    }
}

# =============================================================================
# SECCIÓN 3: MAPEOS DE TRANSFORMACIÓN DE DATOS
# =============================================================================

# Mapeo inteligente de campos Excel a archivo de Norma (con validaciones)
MAPEO_CAMPOS_NORMA = {
    'MAPEOS_DIRECTOS': {
        'Identificador': 'ENLACE',  # Campo "pm" según documentación técnica
        'Norma': 'NORMA',  # Campo "identificador" de la norma aplicable
        'Disposicion': 'TIPO_ADECUACION',  # "retencion o suspensión"
        'Fecha Instalacion\nDD/MM/YYYY': 'FECHA_INSTALACION',
        'Codigo. Transformador (1T,2T,3T,4T,5T)': 'CODIGO_TRAFO',  # Opcional según documentación
        'Altura': 'CANTIDAD'  # Campo altura del Excel se mapea a cantidad
    },
    'VALIDACIONES': {
        'FECHA_INSTALACION': 'Formato DD/MM/YYYY obligatorio',
        'CODIGO_TRAFO': 'Si viene se usa, si no queda vacío (según notas técnicas)',
        'TIPO_ADECUACION': 'Solo valores: RETENCION, SUSPENSION',
        'CANTIDAD': 'Debe ser numérico positivo (altura en metros)'
    }
}

# Mapeo completo y optimizado de campos Excel a campos de salida por tipo
MAPEO_EXCEL_A_SALIDA = {
    'EXPANSION': {
        # Campos geoespaciales (críticos para expansión)
        'Coordenada_X1\nLONGITUD': 'COORDENADA_X',
        'Coordenada_Y1\nLATITUD': 'COORDENADA_Y',
        'Ubicación': 'UBICACION',
        
        # Campos técnicos principales
        'Apoyo': 'GRUPO',
        'Tipo': 'TIPO', 
        'Material': 'CLASE',
        'UC': 'UC',  # Versión normalizada
        'Unidad Constructiva': 'UC',  # Versión original
        'Nivel de Tension': 'NIVEL_TENSION',
        'KGF': 'OT_MAXIMO',
        
        # Campos normativos y administrativos
        'Norma': 'NORMA',
        'Disposicion': 'TIPO_ADECUACION', 
        'Poblacion': 'CLASIFICACION_MERCADO',
        'Tipo Red': 'USO',
        'Tipo inversión': 'TIPO_PROYECTO',
        'Código línea': 'ID_MERCADO',
        'Estado': 'ESTADO',
        
        # Campos de trazabilidad
        'Código FID\nGIT': 'FID_ANTERIOR',
        'Identificador': 'ENLACE',
        'Codigo Inventario': 'CODIGO_MATERIAL',
        
        # Campos temporales y de proyecto
        'Fecha Instalacion\nDD/MM/YYYY': 'FECHA_INSTALACION',
        'Contrato/Soporte': 'PROYECTO',
        
        # Campos descriptivos
        'Nombre': 'PROPIETARIO',
        'OBSERVACION': 'OBSERVACIONES',
        'Altura': 'CANTIDAD'  # Para archivo de norma
    },
    
    'REPOSICION_NUEVO': {
        # Campos identificadores (críticos para reposición)
        'Código FID\nGIT': 'CODIGO_OPERATIVO',
        'Coordenada_X1\nLONGITUD': 'COORDENADA_X',
        'Coordenada_Y1\nLATITUD': 'COORDENADA_Y',
        
        # Campos técnicos heredados o nuevos
        'Apoyo': 'GRUPO',
        'Tipo': 'TIPO',
        'Material': 'CLASE', 
        'UC': 'UC',  # Versión normalizada
        'Unidad Constructiva': 'UC',  # Versión original
        'Nivel de Tension': 'NIVEL_TENSION',
        'KGF': 'OT_MAXIMO',
        'Estado': 'ESTADO',
        
        # Campos administrativos
        'Poblacion': 'CLASIFICACION_MERCADO',
        'Tipo Red': 'USO',
        'Tipo inversión': 'TIPO_PROYECTO', 
        'Norma': 'NORMA',
        'Disposicion': 'TIPO_ADECUACION',
        
        # Campos de proyecto y trazabilidad
        'Fecha Instalacion\nDD/MM/YYYY': 'FECHA_INSTALACION',
        'Contrato/Soporte': 'PROYECTO',
        'Nombre': 'PROPIETARIO',
        'Ubicación': 'UBICACION',
        'Codigo Inventario': 'CODIGO_MATERIAL',
        'Identificador': 'ENLACE',
        'OBSERVACION': 'OBSERVACIONES',
        'Altura': 'CANTIDAD'
    },
    
    'REPOSICION_BAJO': {
        # Campos mínimos para baja de inventario
        'Código FID\nGIT': 'G3E_FID',
        'Fecha Instalacion\nDD/MM/YYYY': 'FECHA_INSTALACION',
        'Fecha Fuera Operacion\nDD/MM/YYYY': 'FECHA_FUERA_OPERACION',
        
        # Campos técnicos para inventario
        'Codigo Inventario': 'CODIGO_MATERIAL',
        'UC': 'UC',  # Versión normalizada
        'Unidad Constructiva': 'UC',  # Versión original
        'Norma': 'NORMA',
        'Tipo Disposicion': 'TIPO_DISPOSICION',
        'OBSERVACION': 'OBSERVACIONES'
    }
}

# =============================================================================
# SECCIÓN 4: CONFIGURACIONES DE TIPOS Y VALIDACIONES
# =============================================================================

# Configuración de tipos de campo para generación XML (con validaciones automáticas)
TIPOS_CAMPOS_XML = {
    # Campos numéricos con validaciones de rango
    'COORDENADA_X': {'tipo': 'decimal', 'rango': [-81, -66], 'precision': 6},  # Longitud Colombia
    'COORDENADA_Y': {'tipo': 'decimal', 'rango': [-5, 16], 'precision': 6},   # Latitud Colombia  
    'CANTIDAD': {'tipo': 'numero', 'rango': [1, 50], 'precision': 1},         # Altura/cantidad en metros
    'PORCENTAJE_PROPIEDAD': {'tipo': 'numero', 'rango': [1, 100], 'precision': 0},
    'G3E_FID': {'tipo': 'numero', 'rango': [1, 999999999], 'precision': 0},   # ID numérico
    'OT_MAXIMO': {'tipo': 'numero', 'rango': [100, 5000], 'precision': 0},    # KGF válidos
    
    # Campos de fecha con validaciones temporales
    'FECHA_INSTALACION': {'tipo': 'fecha', 'formato': 'DD/MM/YYYY', 'rango_anos': [1950, 2030]},
    'FECHA_OPERACION': {'tipo': 'fecha', 'formato': 'DD/MM/YYYY', 'rango_anos': [1950, 2030]},
    'FECHA_FUERA_OPERACION': {'tipo': 'fecha', 'formato': 'DD/MM/YYYY', 'rango_anos': [1950, 2030]},
    
    # Campos texto con longitudes máximas
    'CODIGO_OPERATIVO': {'tipo': 'texto', 'longitud_max': 20, 'patron': r'^[A-Z0-9_-]+$'},
    'UC': {'tipo': 'texto', 'longitud_max': 15, 'patron': r'^N[1-4]L?\d*[A-Z]*$'},
    'NORMA': {'tipo': 'texto', 'longitud_max': 50},
    'ENLACE': {'tipo': 'texto', 'longitud_max': 30},
    'OBSERVACIONES': {'tipo': 'texto', 'longitud_max': 500}
}

# Tipos de estructura unificados (solo 3 categorías tras unificación)
TIPOS_ESTRUCTURA = {
    'EXPANSION': {
        'nombre': 'Expansión',
        'descripcion': 'Nuevas estructuras para ampliación de red',
        'codigo_interno': 'EXP',
        'campos_criticos': ['COORDENADA_X', 'COORDENADA_Y', 'UC', 'NIVEL_TENSION']
    },
    'REPOSICION_NUEVO': {
        'nombre': 'Reposición Nuevo', 
        'descripcion': 'Reemplazo de estructuras existentes',
        'codigo_interno': 'REP_NUE',
        'campos_criticos': ['CODIGO_OPERATIVO', 'COORDENADA_X', 'COORDENADA_Y']
    },
    'REPOSICION_BAJO': {
        'nombre': 'Reposición Bajo',
        'descripcion': 'Retiro y baja de estructuras (incluye desmantelado)',
        'codigo_interno': 'REP_BAJ', 
        'campos_criticos': ['G3E_FID', 'FECHA_INSTALACION', 'FECHA_FUERA_OPERACION'],
        'nota': 'Unifica categorías Reposición Bajo y Desmantelado'
    }
}

# Estados de salud con normalización inteligente y validaciones
ESTADOS_SALUD = {
    'MAPEOS_NUMERICOS': {
        '1': 'BUENO', '2': 'REGULAR', '3': 'MALO'
    },
    'MAPEOS_TEXTUALES': {
        'BUENO': 'BUENO', 'REGULAR': 'REGULAR', 'MALO': 'MALO',
        'BUEN ESTADO': 'BUENO', 'ESTADO REGULAR': 'REGULAR', 'MAL ESTADO': 'MALO',
        'EXCELENTE': 'BUENO', 'ACEPTABLE': 'REGULAR', 'DEFICIENTE': 'MALO',
        'OPTIMO': 'BUENO', 'MEDIO': 'REGULAR', 'CRITICO': 'MALO'
    },
    'VALOR_DEFECTO': 'REGULAR',  # Valor conservador si no se puede determinar
    'VALIDACIONES': {
        'BUENO': 'No requiere intervención inmediata',
        'REGULAR': 'Requiere monitoreo y mantenimiento preventivo', 
        'MALO': 'Requiere intervención correctiva urgente'
    }
}

# Lista optimizada para formularios (solo valores finales)
OPCIONES_ESTADO_SALUD = ['BUENO', 'REGULAR', 'MALO']

# =============================================================================
# SECCIÓN 5: CATÁLOGOS OPERACIONALES
# =============================================================================

# Catálogo completo de circuitos CENS con metadatos geográficos y operacionales
# Fuente: Sistema operacional CENS - Actualizado 2025-08-29
CIRCUITOS_DISPONIBLES = {
    # Región Norte de Santander - Zonas principales
    'CUCUTA_METROPOLITANA': [
        'ABRC1', 'ABRC2', 'ABRC3',  # Circuitos Área Metropolitana Cúcuta
        'BELC21', 'BELC22', 'BELC23', 'BELC24', 'BELC27', 'BELC28', 'BELC29', 
        'BELC30', 'BELC31', 'BELC33', 'BELC35', 'BELC36', 'BELC38'  # Bello
    ],
    'AGUACHICA_ZONA': [
        'AGUC2', 'AGUC3', 'AGUC4', 'AGUC5', 'AGUC7', 'AGUC8',  # Aguachica
        'AGUIG5', 'AGUIG6'  # Aguachica Industrial
    ],
    'OCANA_ZONA': [
        'OCAIA15', 'OCAIC25', 'OCAILA5', 'OCALA_PLAYA',
        'OCAOCANA1', 'OCAOCANA2', 'OCAOCANA3', 'OCAGONZA'  # Ocaña y alrededores
    ],
    'PAMPLONA_ZONA': [
        'PAMC2', 'PAMC3', 'PAMC4',  # Pamplona Centro
        'PATC1', 'PATC2', 'PATC3'   # Pamplonita
    ],
    'SARDINATA_ZONA': [
        'SARC1', 'SARC2',  # Sardinata
        'SANC43', 'SANC45', 'SANC46', 'SANC48', 'SANC49', 'SANC51', 
        'SANC52', 'SANC53', 'SANC54', 'SANC55', 'SANC56', 'SANC57', 
        'SANC58', 'SANC59'  # San Calixto
    ],
    'OTROS_MUNICIPIOS': [
        'ATAC86', 'ATAC87', 'ATAC88',  # Ábrego
        'AYAA31', 'AYAC1', 'AYAC2',    # Villa del Rosario
        'BUIA25', 'BUIA45', 'BUTC1', 'BUTC2',  # Bucarasica
        'CACHIRA', 'CAMC1', 'CAMC2', 'CAMC3',  # Cachirá
        'CLIL20', 'CONS65', 'CONS75', 'CONS95', 'CONVENCION',  # Convención
        'CORC1', 'CORC2', 'CORC3',     # Convención rural
        'CULC1', 'CULC2',              # Cúcutilla
        'ELCARMEN', 'ELSC68', 'ELSC69',  # El Carmen
        'ESCC61', 'ESCC62', 'ESCC63',    # Espíritu Santo
        'GAMC1', 'GAMC2', 'GAMC3',       # Gamarra
        'GRAC1', 'GRAC2', 'GRAC3',       # Gramalote
        'IL70', 'INSC76', 'INSC77', 'INSC91', 'INSC92', 'INSC93', 'INSC94', 'INSIL60',  # Zona Industrial
        'ORUC1', 'ORUC2',                # Ortega
        'PELC1', 'PELC2',                # Pelaya
        'PIL30', 'PLZS10', 'PLZS20', 'PLZ263B1', 'PLZ283B1',  # Plaza
        'SALC1', 'SALC2', 'SALC3', 'SALC4',  # Salazar
        'SEVC11', 'SEVC16', 'SEVC17', 'SEVC21', 'SEVC22', 'SEVC3', 'SEVC4', 'SEVC5', 'SEVC6', 'SEVC7',
        'SEVS10', 'SEVS20',              # Sevilla
        'SPAC1', 'SPAC2',                # San Pedro
        'SRQC1', 'SRQC2', 'SRQC3',      # San Rafael
        'TARC1', 'TARC2',                # Taraza
        'ZULC1', 'ZULC2', 'ZULC3'       # Zulia
    ],
    # Circuitos especiales y proyectos
    'ESPECIALES': [
        'FIBRA OPT',     # Fibra óptica
        'GABGABARRA',    # Gabarra especial
        'LA MIEL', 'LAMATA', 'LOS ALPES', 'LOS MANGOS', 'MONTESITOS',  # Proyectos especiales
        'SAMSAMORE', 'SANALBERTO', 'SANANTONIO',  # San Alberto zona
        'SANIL15', 'SANOL15', 'SANOL25', 'SANOL35', 'SANOL45', 'SANOL55',  # San Onofre
        'TEORAMA',       # Teorama
        'TIBCAMP2', 'TIBG11', 'TIBO11', 'TIBPOZOS', 'TIBTIBU1', 'TIBTIBU2', 'TIBTIBU3',  # Tibú
        'TOLLABATEC', 'TOLPALERMO', 'TOLTOLEDO'  # Toledo zona
    ],
    # Circuitos palmeros (especiales por ubicación)
    'ZONA_PALMERA': [
        'PALBOCHA', 'PALCHINA', 'PALDONJU', 'PALRAGON'
    ]
}

# Lista plana para compatibilidad con código existente (auto-generada)
CIRCUITOS_LISTA_PLANA = []
for zona, circuitos in CIRCUITOS_DISPONIBLES.items():
    CIRCUITOS_LISTA_PLANA.extend(circuitos)

# =============================================================================
# SECCIÓN 6: CATÁLOGO DE MATERIALES Y SISTEMA DE MAPEO UC
# =============================================================================

# Catálogo completo de códigos de materiales con clasificación inteligente
# Organizado por tipo de material y capacidad para facilitar búsquedas
CATALOGO_MATERIALES = {
    'INDICES_BUSQUEDA': {
        # Índice inverso: de código a descripción (para O(1) lookup)
        'POR_CODIGO': {},  # Se llena automáticamente al final
        # Índice por altura (para selección inteligente)
        'POR_ALTURA': {
            '8M': [], '10M': [], '12M': [], '14M': [], '16M': [], '18M': [], '20M': [], '22M': [], '24M': []
        },
        # Índice por capacidad KGF (para selección por carga)
        'POR_CAPACIDAD': {
            '510KGF': [], '750KGF': [], '1050KGF': [], '1350KGF': [], '1500KGF': [], '2000KGF': [], '3000KGF': [], '4000KGF': []
        }
    },
    
    'POSTES_CONCRETO': {
        # 8 metros
        '200002': 'POSTE CONCRETO 8M 510KGF',
        '200003': 'POSTE CONCRETO 8M 750KGF',
        '200004': 'POSTE CONCRETO 8M 1050KGF',
        '200005': 'POSTE CONCRETO 8M 1350KGF',
        '200006': 'POSTE CONCRETO 8M 1500KGF',
        '215651': 'POSTE CONCRETO 8M 1800KGF',
        '200007': 'POSTE CONCRETO 8M 2000KGF',
        
        # 10 metros (más comunes)
        '200009': 'POSTE CONCRETO 10M 510KGF',
        '200010': 'POSTE CONCRETO 10M 750KGF',
        '200011': 'POSTE CONCRETO 10M 1050KGF',
        '215652': 'POSTE CONCRETO 10M 1350KGF',
        '200012': 'POSTE CONCRETO 10M 1500KGF',
        '215653': 'POSTE CONCRETO 10M 1800KGF',
        '254294': 'POSTE CONCRETO 10M 2000KGF',
        
        # 12 metros
        '200013': 'POSTE CONCRETO 12M 510KGF',
        '200015': 'POSTE CONCRETO 12M 750KGF',
        '200016': 'POSTE CONCRETO 12M 1050KGF',
        '200017': 'POSTE CONCRETO 12M 1350KGF',
        '200018': 'POSTE CONCRETO 12M 1500KGF',
        '200019': 'POSTE CONCRETO 12M 2000KGF',
        '200020': 'POSTE CONCRETO 12M 3000KGF',
        '200021': 'POSTE CONCRETO 12M 4000KGF',
        '200014': 'POSTE CONCRETO 12M 200DAN AP',
        
        # 14 metros (muy comunes para primario)
        '200022': 'POSTE CONCRETO 14M 750KGF',
        '200023': 'POSTE CONCRETO 14M 1050KGF',
        '215641': 'POSTE CONCRETO 14M 1050KGF',
        '200024': 'POSTE CONCRETO 14M 1350KGF',
        '200025': 'POSTE CONCRETO 14M 1500KGF',
        '200026': 'POSTE CONCRETO 14M 2000KGF',
        '249508': 'POSTE CONCRETO 14M 2000KGF',
        '200027': 'POSTE CONCRETO 14M 3000KGF',
        '200028': 'POSTE CONCRETO 14M 4500KGF',
        
        # 16 metros y superiores
        '200029': 'POSTE CONCRETO 16M 750KGF',
        '200031': 'POSTE CONCRETO 16M 1050KGF',
        '200032': 'POSTE CONCRETO 16M 1350KGF',
        '200033': 'POSTE CONCRETO 16M 1500KGF',
        '214623': 'POSTE CONCRETO 16M 2000KGF',
        '231315': 'POSTE CONCRETO 16M 2000KGF',
        '215643': 'POSTE CONCRETO 16M 3000KGF',
        '231316': 'POSTE CONCRETO 16M 3000KGF',
        '231317': 'POSTE CONCRETO 16M 4000KGF',
        '249509': 'POSTE CONCRETO 16M 4000KGF',
        '200030': 'POSTE CONCRETO 16M 300DAN AP',
        
        # Alturas especiales
        '215644': 'POSTE CONCRETO 18M 3000KGF',
        '249510': 'POSTE CONCRETO 20M 4000KGF',
        '200034': 'POSTE CONCRETO 26M 1050KGF',
        
        # Alumbrado público especiales
        '200000': 'POSTE CONCRETO 5M 140DAN AP',
        '200001': 'POSTE CONCRETO 5M 350KGF AP',
        '200008': 'POSTE CONCRETO 9M 200DAN AP'
    },
    
    'POSTES_METALICOS': {
        # Alumbrado público
        '226592': 'POSTE METALICO 3M AP',
        '226591': 'POSTE METALICO 3.5M AP',
        '200071': 'POSTE METALICO 4M AP',
        '220332': 'POSTE METALICO 4.2M 150KGF AP',
        '200072': 'POSTE METALICO 4.5M AP',
        '200073': 'POSTE METALICO 5.11M AP',
        '200074': 'POSTE METALICO 6M AP',
        
        # Distribución estándar 8M
        '200075': 'POSTE METALICO 8M 350KGF',
        '200076': 'POSTE METALICO 8M 510KGF',
        '200077': 'POSTE METALICO 8M 750KGF',
        '200078': 'POSTE METALICO 8M 1050KGF',
        
        # Distribución 10M-12M
        '200079': 'POSTE METALICO 10M 510KGF',
        '214746': 'POSTE METALICO 10M 750KGF',
        '214747': 'POSTE METALICO 10M 1050KGF',
        '214748': 'POSTE METALICO 10M 1350KGF',
        '200080': 'POSTE METALICO 12M 510KGF',
        '200081': 'POSTE METALICO 12M 750KGF',
        '200082': 'POSTE METALICO 12M 1050KGF',
        '214749': 'POSTE METALICO 12M 1350KGF',
        
        # Distribución 14M-18M
        '200083': 'POSTE METALICO 14M 750KGF',
        '200084': 'POSTE METALICO 14M 1050KGF',
        '214750': 'POSTE METALICO 14M 1350KGF',
        '214751': 'POSTE METALICO 14M 1500KGF',
        '214752': 'POSTE METALICO 16M 750KGF',
        '200085': 'POSTE METALICO 16M 1050KGF',
        '214753': 'POSTE METALICO 16M 1350KGF',
        '218494': 'POSTE METALICO 16M 1500KGF',
        '218493': 'POSTE METALICO 16M 2000KGF',
        '218490': 'POSTE METALICO 16M 3000KGF',
        '229391': 'POSTE METALICO 16M',
        '232126': 'POSTE METALICO 16M',
        '229390': 'POSTE METALICO 17M',
        '200086': 'POSTE METALICO 18M 1050KGF',
        '200087': 'POSTE METALICO 18M 1350KGF',
        '218495': 'POSTE METALICO 18M 2000KGF',
        '215023': 'POSTE METALICO 18M 2500KGF',
        '218491': 'POSTE METALICO 18M 3000KGF',
        
        # Transmisión y especiales
        '229388': 'POSTE METALICO 20M',
        '229389': 'POSTE METALICO 20M',
        '214754': 'POSTE METALICO 20M 1050KGF',
        '214755': 'POSTE METALICO 20M 1350KGF',
        '229387': 'POSTE METALICO 22M',
        '214756': 'POSTE METALICO 22M 1050KGF',
        '214757': 'POSTE METALICO 22M 1350KGF',
        '214758': 'POSTE METALICO 24M 1350KGF',
        '222328': 'POSTE METALICO 25M',
        '222327': 'POSTE METALICO 26.5M',
        '222325': 'POSTE METALICO 31M',
        '222326': 'POSTE METALICO 31M',
        '246855': 'POSTE METALICO1.70M ORNAMENTAL'
    },
    
    'POSTES_MADERA': {
        '200088': 'POSTE MADERA 8M 510KGF',
        '200089': 'POSTE MADERA 10M 510KGF',
        '200090': 'POSTE MADERA 12M 510KGF'
    },
    
    'POSTES_PRFV': {
        # Alumbrado público PRFV
        '200035': 'POSTE PRFV 5.5M 150KGF AP',
        '200036': 'POSTE PRFV 6M 250KGF AP',
        '200037': 'POSTE PRFV 7.5M 350KGF AP',
        '200038': 'POSTE PRFV 7.5M 350KGF AP',
        '200046': 'POSTE PRFV 9M 250KGF AP',
        '200047': 'POSTE PRFV 9M 350KGF AP',
        '200048': 'POSTE PRFV 9M 350KGF AP TRASLU',
        '200053': 'POSTE PRFV 10.2M 350KGF AP',
        '200054': 'POSTE PRFV 10.2M 350KGF AP',
        '200055': 'POSTE PRFV 12M 350KGF AP',
        '200091': 'POSTE PRFV 10M 200KGF AP',
        
        # Distribución PRFV 8M
        '200039': 'POSTE PRFV 8M 350KGF',
        '200040': 'POSTE PRFV 8M 510KGF',
        '200041': 'POSTE PRFV 8M 510KGF',
        '200042': 'POSTE PRFV 8M 750KGF',
        '200043': 'POSTE PRFV 8M 750KGF',
        '200044': 'POSTE PRFV 8M 1050KGF',
        '200045': 'POSTE PRFV 8M 1050KGF',
        
        # Distribución PRFV 10M-12M
        '200049': 'POSTE PRFV 10M 510KGF',
        '200050': 'POSTE PRFV 10M 510KGF',
        '200051': 'POSTE PRFV 10M 1050KGF',
        '200052': 'POSTE PRFV 10M 1050KGF',
        '215646': 'POSTE PRFV 10M 750KGF',
        '215647': 'POSTE PRFV 10M 750KGF',
        '200056': 'POSTE PRFV 12M 510KGF',
        '200057': 'POSTE PRFV 12M 510KGF',
        '200058': 'POSTE PRFV 12M 750KGF',
        '200059': 'POSTE PRFV 12M 750KGF',
        '200060': 'POSTE PRFV 12M 1050KGF',
        '200061': 'POSTE PRFV 12M 1050KGF',
        '200062': 'POSTE PRFV 12M 1350KGF',
        '200063': 'POSTE PRFV 12M 1350KGF',
        
        # Distribución PRFV 14M-20M
        '200064': 'POSTE PRFV 14M 750KGF',
        '200065': 'POSTE PRFV 14M 750KGF',
        '200066': 'POSTE PRFV 14M 1050KGF',
        '215648': 'POSTE PRFV 14M 1050KGF',
        '200067': 'POSTE PRFV 14M 1350KGF',
        '291313': 'POSTE PRFV 14M 1350KGF MONOLITICO',
        '215649': 'POSTE PRFV 16M 750KGF',
        '215232': 'POSTE PRFV 16M 1050KGF',
        '200068': 'POSTE PRFV 16M 1350KGF',
        '231314': 'POSTE PRFV 16M 1500KGF',
        '214946': 'POSTE PRFV 16M 2000KGF',
        '200069': 'POSTE PRFV 18M 1050KGF',
        '200070': 'POSTE PRFV 18M 1350KGF',
        '260460': 'POSTE PRFV 20M 1050KGF'
    }
}

# =============================================================================
# SECCIÓN 7: SISTEMA INTELIGENTE DE MAPEO UC-MATERIAL
# =============================================================================

# Sistema inteligente de mapeo UC a código de material con múltiples estrategias
MAPEO_UC_MATERIAL = {
    'ESTRATEGIAS_MAPEO': {
        'PRIORIDAD': [
            'MAPEOS_DIRECTOS',          # Más específico
            'PATRONES_REGEX',           # Reglas de patrón
            'INFERENCIA_INTELIGENTE',   # Lógica basada en campos
            'VALORES_DEFECTO'           # Fallback
        ]
    },
    
    # Mapeos directos de UC conocidas (alta confianza)
    'MAPEOS_DIRECTOS': {
        # Niveles N3 (más comunes)
        'N3L75': '200022',   # POSTE CONCRETO 14M 750KGF
        'N3L79': '200023',   # POSTE CONCRETO 14M 1050KGF  
        'N3L78': '200022',   # POSTE CONCRETO 14M 750KGF
        'N3L105': '200023',  # POSTE CONCRETO 14M 1050KGF
        'N3L135': '200024',  # POSTE CONCRETO 14M 1350KGF
        
        # Niveles N2 (distribución media)
        'N2L75': '200015',   # POSTE CONCRETO 12M 750KGF
        'N2L79': '200016',   # POSTE CONCRETO 12M 1050KGF
        'N2L105': '200016',  # POSTE CONCRETO 12M 1050KGF
        'N2L135': '200017',  # POSTE CONCRETO 12M 1350KGF
        
        # Niveles N1 (baja tensión)
        'N1L51': '200013',   # POSTE CONCRETO 12M 510KGF
        'N1L75': '200015',   # POSTE CONCRETO 12M 750KGF
        'N1L105': '200016',  # POSTE CONCRETO 12M 1050KGF
        
        # Niveles N4 (alta tensión)
        'N4L105': '200031',  # POSTE CONCRETO 16M 1050KGF
        'N4L135': '200032',  # POSTE CONCRETO 16M 1350KGF
        'N4L200': '214623',  # POSTE CONCRETO 16M 2000KGF
    },
    
    # Patrones regex para UCs con estructura predecible
    'PATRONES_REGEX': [
        {
            'patron': r'^N([1-4])L?(\d{2,3})([A-Z]*)$',
            'descripcion': 'UC estándar: N[nivel]L[carga opcional][sufijo]',
            'logica_mapeo': {
                'N1': {  # Secundario -> 12M típicamente
                    '51': '200013',   # 12M 510KGF
                    '75': '200015',   # 12M 750KGF
                    '79': '200016',   # 12M 1050KGF (79 ≈ 1050/13.4)
                    'defecto': '200015'  # 12M 750KGF por defecto
                },
                'N2': {  # Primario bajo -> 12M-14M
                    '75': '200015',   # 12M 750KGF
                    '79': '200016',   # 12M 1050KGF
                    '105': '200023',  # 14M 1050KGF (más robusto)
                    'defecto': '200016'  # 12M 1050KGF por defecto
                },
                'N3': {  # Primario estándar -> 14M típicamente
                    '75': '200022',   # 14M 750KGF
                    '78': '200022',   # 14M 750KGF
                    '79': '200023',   # 14M 1050KGF
                    '105': '200023',  # 14M 1050KGF
                    '135': '200024',  # 14M 1350KGF
                    'defecto': '200023'  # 14M 1050KGF por defecto
                },
                'N4': {  # Primario alto -> 16M típicamente
                    '105': '200031',  # 16M 1050KGF
                    '135': '200032',  # 16M 1350KGF
                    '150': '200033',  # 16M 1500KGF
                    '200': '214623',  # 16M 2000KGF
                    'defecto': '200031'  # 16M 1050KGF por defecto
                }
            }
        },
        {
            'patron': r'.*(\d{1,2})M.*(\d{3,4})KGF.*',
            'descripcion': 'UC con altura y carga explícitas',
            'logica_mapeo': 'buscar_por_altura_y_capacidad'
        }
    ],
    
    # Sistema de inferencia inteligente basado en múltiples campos
    'INFERENCIA_INTELIGENTE': {
        'REGLAS_COMBINADAS': [
            {
                'condiciones': {'NIVEL_TENSION': 'N1L', 'TIPO': 'SECUNDARIO'},
                'material_sugerido': '200015',  # 12M 750KGF (estándar secundario)
                'confianza': 0.8
            },
            {
                'condiciones': {'NIVEL_TENSION': ['N2L', 'N3L'], 'TIPO': 'PRIMARIO'},
                'material_sugerido': '200023',  # 14M 1050KGF (estándar primario)
                'confianza': 0.9
            },
            {
                'condiciones': {'NIVEL_TENSION': 'N4L', 'TIPO': 'PRIMARIO'},
                'material_sugerido': '200031',  # 16M 1050KGF (alta tensión)
                'confianza': 0.9
            },
            {
                'condiciones': {'OT_MAXIMO': range(500, 800)},  # 510-750 KGF
                'materiales_candidatos': ['200013', '200015', '200022'],
                'seleccionar_por': 'NIVEL_TENSION'
            },
            {
                'condiciones': {'OT_MAXIMO': range(800, 1200)},  # 1050 KGF aprox
                'materiales_candidatos': ['200016', '200023', '200031'],
                'seleccionar_por': 'NIVEL_TENSION'
            }
        ]
    },
    
    # Valores por defecto jerárquicos (cuando falla todo lo anterior)
    'VALORES_DEFECTO': {
        'POR_TIPO_ESTRUCTURA': {
            'EXPANSION': '200023',        # 14M 1050KGF (robusto para nuevas)
            'REPOSICION_NUEVO': '200023', # 14M 1050KGF (estándar)
            'REPOSICION_BAJO': '200015'   # 12M 750KGF (típico retirado)
        },
        'POR_NIVEL_TENSION': {
            'N1L': '200015',  # 12M 750KGF
            'N2L': '200016',  # 12M 1050KGF
            'N3L': '200023',  # 14M 1050KGF
            'N4L': '200031'   # 16M 1050KGF
        },
        'POR_TIPO': {
            'SECUNDARIO': '200015',  # 12M 750KGF
            'PRIMARIO': '200023'     # 14M 1050KGF
        },
        'UNIVERSAL': '200023'  # 14M 1050KGF (más versátil)
    }
}

# =============================================================================
# SECCIÓN 8: INICIALIZACIÓN AUTOMÁTICA DE ÍNDICES
# =============================================================================

# Auto-construcción de índices de búsqueda para optimización
def _construir_indices_materiales():
    """Construye automáticamente los índices de búsqueda del catálogo"""
    import re
    
    todos_materiales = {}
    indices_altura = {}
    indices_capacidad = {}
    
    # Combinar todos los materiales
    for categoria, materiales in CATALOGO_MATERIALES.items():
        if categoria != 'INDICES_BUSQUEDA':
            todos_materiales.update(materiales)
    
    # Construir índices
    for codigo, descripcion in todos_materiales.items():
        # Extraer altura
        match_altura = re.search(r'(\d+)M', descripcion)
        if match_altura:
            altura = f"{match_altura.group(1)}M"
            if altura not in indices_altura:
                indices_altura[altura] = []
            indices_altura[altura].append(codigo)
        
        # Extraer capacidad
        match_capacidad = re.search(r'(\d+)KGF', descripcion)
        if match_capacidad:
            capacidad = f"{match_capacidad.group(1)}KGF"
            if capacidad not in indices_capacidad:
                indices_capacidad[capacidad] = []
            indices_capacidad[capacidad].append(codigo)
    
    return todos_materiales, indices_altura, indices_capacidad

# Ejecutar construcción automática
_todos_materiales, _indices_altura, _indices_capacidad = _construir_indices_materiales()

# Actualizar índices en el catálogo
CATALOGO_MATERIALES['INDICES_BUSQUEDA']['POR_CODIGO'] = _todos_materiales
CATALOGO_MATERIALES['INDICES_BUSQUEDA']['POR_ALTURA'].update(_indices_altura)
CATALOGO_MATERIALES['INDICES_BUSQUEDA']['POR_CAPACIDAD'].update(_indices_capacidad)

# =============================================================================
# SECCIÓN 9: UTILIDADES Y FUNCIONES HELPER
# =============================================================================

# Funciones de utilidad para acceso rápido (pueden usarse desde servicios)
def obtener_material_por_codigo(codigo):
    """Busqueda O(1) de material por código"""
    return CATALOGO_MATERIALES['INDICES_BUSQUEDA']['POR_CODIGO'].get(codigo, f'Material {codigo} no encontrado')

def buscar_materiales_por_altura(altura):
    """Buscar todos los materiales de una altura específica"""
    return CATALOGO_MATERIALES['INDICES_BUSQUEDA']['POR_ALTURA'].get(altura, [])

def buscar_materiales_por_capacidad(capacidad):
    """Buscar todos los materiales de una capacidad específica"""
    return CATALOGO_MATERIALES['INDICES_BUSQUEDA']['POR_CAPACIDAD'].get(capacidad, [])

def obtener_circuitos_por_zona(zona):
    """Obtener circuitos de una zona geográfica específica"""
    return CIRCUITOS_DISPONIBLES.get(zona, [])

# Mantener compatibilidad con código existente
CIRCUITOS_DISPONIBLES_LISTA = CIRCUITOS_LISTA_PLANA
