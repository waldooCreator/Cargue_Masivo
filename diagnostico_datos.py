#!/usr/bin/env python3
"""
Script de diagnóstico para verificar procesamiento de datos
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura

def diagnosticar_ultimo_proceso():
    """Diagnostica el último proceso ejecutado"""
    try:
        ultimo_proceso = ProcesoEstructura.objects.filter(
            estado__in=['COMPLETADO', 'CLASIFICADO']
        ).order_by('-created_at').first()
        
        if not ultimo_proceso:
            print("No hay procesos completados para diagnosticar")
            return
        
        print(f"=== DIAGNÓSTICO PROCESO {ultimo_proceso.id} ===")
        print(f"Estado: {ultimo_proceso.estado}")
        print(f"Clasificación: {ultimo_proceso.clasificacion_automatica}")
        print(f"Circuito: {ultimo_proceso.circuito}")
        
        # Verificar datos_excel (originales)
        if ultimo_proceso.datos_excel:
            print(f"\n--- DATOS EXCEL (primeros 2 registros) ---")
            for i, registro in enumerate(ultimo_proceso.datos_excel[:2]):
                print(f"Registro {i+1}:")
                campos_importantes = ['UC', 'Codigo Inventario', 'COORDENADA_X', 'COORDENADA_Y', 'TIPO_PROYECTO']
                for campo in campos_importantes:
                    valor = registro.get(campo, 'NO_ENCONTRADO')
                    print(f"  {campo}: {valor}")
        
        # Verificar datos_norma (procesados)
        if ultimo_proceso.datos_norma:
            print(f"\n--- DATOS NORMA (primeros 2 registros) ---")
            for i, registro in enumerate(ultimo_proceso.datos_norma[:2]):
                print(f"Registro {i+1}:")
                campos_importantes = ['UC', 'CODIGO_MATERIAL', 'COORDENADA_X', 'COORDENADA_Y', 'TIPO_PROYECTO', 'TIPO']
                for campo in campos_importantes:
                    valor = registro.get(campo, 'NO_ENCONTRADO')
                    print(f"  {campo}: {valor}")
                    
    except Exception as e:
        print(f"Error en diagnóstico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnosticar_ultimo_proceso()
