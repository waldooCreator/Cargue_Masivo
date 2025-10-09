#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de Clasificación Automática de Estructuras Eléctricas
Clasifica automáticamente las estructuras según los campos poblados en el Excel
"""

from typing import Dict, List, Optional
import pandas as pd
from dataclasses import dataclass
import re


@dataclass
class ClasificacionResultado:
    """Resultado de la clasificación de una estructura"""
    tipo: str  # EXPANSION, REPOSICION_NUEVO, REPOSICION_BAJO
    tipo_inversion: str  # T1, T2, T3, T4
    fid_anterior: str
    datos: Dict
    indice: int  # Índice en el DataFrame original


class ClasificadorAutomatico:
    """
    Sistema de clasificación automática de estructuras
    
    Reglas de clasificación:
    1. EXPANSIÓN: Solo campos nuevos (sin FID_ANTERIOR) -> T2/T4
    2. REPOSICIÓN NUEVO: Campos salida + nuevos con mejora (con FID_ANTERIOR) -> T1/T3  
    3. REPOSICIÓN BAJO: Reemplazos simples (incluye desmantelado) -> T1/T3
    """
    
    def __init__(self):
        # Campos que indican estructura de salida (retirada)
        self.campos_salida = [
            'Código FID_rep', 
            'Número de conductores_rep', 
            'Cantidad_rep', 
            'Rpp_rep', 
            'Año entrada operación_rep',
            'Tipo inventario',
            'Codigo UC_rep',
            'DESCRIPCION_rep'
        ]
        
        # Campos que indican estructura nueva (entrante)
        self.campos_nuevo = [
            'Norma', 'Apoyo', 'Tipo', 'Material', 'Altura',
            'Poblacion', 'Disposicion', 'KGF', 'Tipo Red',
            'Codigo Inventario', 'Fecha Instalacion',
            'Unidad Constructiva', 'Identificador', 'DESCRIPCION'
        ]
    
    def clasificar_dataset(self, df: pd.DataFrame) -> Dict[str, List[ClasificacionResultado]]:
        """
        Clasifica todo el dataset y agrupa por tipo
        
        Returns:
            Dict con listas de resultados por tipo:
            - EXPANSION: []
            - REPOSICION_NUEVO: []
            - REPOSICION_BAJO: [] (incluye casos de solo retiro/desmantelado)
        """
        resultados = {
            'EXPANSION': [],
            'REPOSICION_NUEVO': [],
            'REPOSICION_BAJO': [],
            'SIN_CLASIFICAR': []
        }
        
        for idx, fila in df.iterrows():
            clasificacion = self.clasificar_registro(fila, idx)
            if clasificacion.tipo in resultados:
                resultados[clasificacion.tipo].append(clasificacion)
        
        return resultados
    
    def clasificar_registro(self, fila: pd.Series, indice: int = 0) -> ClasificacionResultado:
        """
        Clasifica un registro individual según las reglas de negocio
        """
        tiene_salida = self._tiene_datos(fila, self.campos_salida)
        tiene_nuevo = self._tiene_datos(fila, self.campos_nuevo)
        
        # Determinar tipo de operación según campos poblados
        if tiene_salida and tiene_nuevo:
            # CAMBIO DE POSTE (Reposición)
            tipo = self._clasificar_reposicion(fila)
            tipo_inversion = self._determinar_tipo_inversion_reposicion(fila)
            fid_anterior = str(fila.get('Código FID_rep', ''))  # FID del poste retirado
            
        elif tiene_salida and not tiene_nuevo:
            # REPOSICIÓN BAJO (incluye desmantelado - solo retiro)
            tipo = "REPOSICION_BAJO"
            tipo_inversion = "T3"  # Reposición bajo tensión
            fid_anterior = str(fila.get('Código FID_rep', ''))  # FID del poste retirado
            
        elif not tiene_salida and tiene_nuevo:
            # EXPANSIÓN (poste nuevo)
            tipo = "EXPANSION"
            tipo_inversion = self._determinar_tipo_inversion_expansion(fila)
            fid_anterior = ""  # Expansión NUNCA tiene FID_ANTERIOR
            
        else:
            # Registro vacío o incompleto
            tipo = "SIN_CLASIFICAR"
            tipo_inversion = ""
            fid_anterior = ""
        
        return ClasificacionResultado(
            tipo=tipo,
            tipo_inversion=tipo_inversion,
            fid_anterior=fid_anterior,
            datos=fila.to_dict(),
            indice=indice
        )
    
    def _tiene_datos(self, fila: pd.Series, campos: List[str]) -> bool:
        """
        Verifica si al menos uno de los campos tiene datos válidos
        """
        # Mapeo de nombres de campos para manejar encabezados genéricos
        mapeo_campos = {
            'Unidad Constructiva': ['Unidad Constructiva', 'Unnamed: 25'],
            'Codigo Inventario': ['Codigo Inventario', 'Unnamed: 23'],
            'Coordenada_X1\nLONGITUD': ['Coordenada_X1\nLONGITUD', 'Unnamed: 0'],
            'Coordenada_Y1\nLATITUD': ['Coordenada_Y1\nLATITUD', 'Unnamed: 1']
        }
        
        for campo in campos:
            # Obtener lista de posibles nombres para este campo
            posibles_nombres = mapeo_campos.get(campo, [campo])
            
            for nombre in posibles_nombres:
                if nombre in fila:
                    valor = fila[nombre]
                    if pd.notna(valor) and str(valor).strip() and str(valor).strip().lower() != 'nan':
                        return True
        return False
    
    def _obtener_valor_campo(self, fila: pd.Series, campo: str) -> str:
        """
        Obtiene el valor de un campo aplicando mapeo de nombres
        """
        # Mapeo de nombres de campos para manejar encabezados genéricos
        mapeo_campos = {
            'Unidad Constructiva': ['Unidad Constructiva', 'Unnamed: 25'],
            'Codigo Inventario': ['Codigo Inventario', 'Unnamed: 23'],
            'Coordenada_X1\nLONGITUD': ['Coordenada_X1\nLONGITUD', 'Unnamed: 0'],
            'Coordenada_Y1\nLATITUD': ['Coordenada_Y1\nLATITUD', 'Unnamed: 1'],
            'Poblacion': ['Poblacion', 'Unnamed: 19']
        }
        
        # Obtener lista de posibles nombres para este campo
        posibles_nombres = mapeo_campos.get(campo, [campo])
        
        for nombre in posibles_nombres:
            if nombre in fila:
                valor = fila[nombre]
                if pd.notna(valor):
                    return str(valor).strip()
        return ''
    
    def _clasificar_reposicion(self, fila: pd.Series) -> str:
        """
        Determina si es reposición nuevo (mejora) o bajo (reemplazo simple)
        Compara KGF y Altura entre poste saliente y entrante
        """
        try:
            # Extraer valores del poste saliente (retirado)
            uc_salida = str(fila.get('Codigo UC_rep', ''))
            kgf_salida = self._extraer_kgf_de_uc(uc_salida)
            altura_salida = self._extraer_altura_de_uc(uc_salida)
            
            # Valores del poste nuevo (entrante)
            kgf_nuevo = float(fila.get('KGF', 0))
            altura_nuevo = float(fila.get('Altura', 0))
            
            # Si hay mejora en KGF o Altura es REPOSICION_NUEVO
            if kgf_nuevo > kgf_salida or altura_nuevo > altura_salida:
                return "REPOSICION_NUEVO"
            else:
                return "REPOSICION_BAJO"
                
        except (ValueError, TypeError):
            # Si hay error en la comparación, asumir reposición bajo
            return "REPOSICION_BAJO"
    
    def _determinar_tipo_inversion_reposicion(self, fila: pd.Series) -> str:
        """
        Para REPOSICIÓN (con FID_ANTERIOR): T1 o T3
        T1: Reposición en zona urbana o crítica
        T3: Reposición en zona rural o normal
        """
        poblacion = str(fila.get('Poblacion', '')).upper().strip()
        if poblacion in ['URBANA', 'URBANO', 'CRITICA', 'CRÍTICA']:
            return "T1"
        else:
            return "T3"
    
    def _determinar_tipo_inversion_expansion(self, fila: pd.Series) -> str:
        """
        Para EXPANSIÓN (sin FID_ANTERIOR): T2 o T4
        T2: Expansión en zona urbana o crítica  
        T4: Expansión en zona rural o normal
        """
        poblacion = self._obtener_valor_campo(fila, 'Poblacion').upper()
        if poblacion in ['URBANA', 'URBANO', 'CRITICA', 'CRÍTICA']:
            return "T2"
        else:
            return "T4"
    
    def _extraer_kgf_de_uc(self, uc: str) -> float:
        """
        Extrae el valor KGF de la UC (ej: N1L510 -> 510)
        """
        if not uc:
            return 0
        match = re.search(r'(\d+)$', uc)
        if match:
            return float(match.group(1))
        return 0
    
    def _extraer_altura_de_uc(self, uc: str) -> float:
        """
        Extrae la altura típica de la UC según el tipo
        N1L -> 8m, N2L -> 10m, N3L -> 12m, N4L -> 14m
        """
        if not uc:
            return 0
            
        alturas_uc = {
            'N1L': 8,
            'N2L': 10, 
            'N3L': 12,
            'N4L': 14
        }
        
        for prefix, altura in alturas_uc.items():
            if uc.startswith(prefix):
                return altura
        return 0
    
    def generar_resumen(self, resultados: Dict[str, List[ClasificacionResultado]]) -> Dict:
        """
        Genera un resumen estadístico de la clasificación
        """
        total = sum(len(lista) for lista in resultados.values())
        
        return {
            'total_registros': total,
            'expansion': {
                'cantidad': len(resultados['EXPANSION']),
                'porcentaje': round(len(resultados['EXPANSION']) / total * 100, 1) if total > 0 else 0,
                'tipos_inversion': self._contar_tipos_inversion(resultados['EXPANSION'])
            },
            'reposicion_nuevo': {
                'cantidad': len(resultados['REPOSICION_NUEVO']),
                'porcentaje': round(len(resultados['REPOSICION_NUEVO']) / total * 100, 1) if total > 0 else 0,
                'tipos_inversion': self._contar_tipos_inversion(resultados['REPOSICION_NUEVO'])
            },
            'reposicion_bajo': {
                'cantidad': len(resultados['REPOSICION_BAJO']),
                'porcentaje': round(len(resultados['REPOSICION_BAJO']) / total * 100, 1) if total > 0 else 0,
                'tipos_inversion': self._contar_tipos_inversion(resultados['REPOSICION_BAJO']),
                'incluye_retiros': True  # Indica que incluye casos de solo retiro/desmantelado
            },
            'sin_clasificar': {
                'cantidad': len(resultados['SIN_CLASIFICAR']),
                'porcentaje': round(len(resultados['SIN_CLASIFICAR']) / total * 100, 1) if total > 0 else 0
            }
        }
    
    def _contar_tipos_inversion(self, resultados: List[ClasificacionResultado]) -> Dict[str, int]:
        """Cuenta los tipos de inversión en una lista de resultados"""
        conteo = {}
        for resultado in resultados:
            tipo = resultado.tipo_inversion
            conteo[tipo] = conteo.get(tipo, 0) + 1
        return conteo
