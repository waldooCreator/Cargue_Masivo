#!/usr/bin/env python3
"""
Test de flujo completo de UC
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.models import ProcesoEstructura

def test_flujo_uc():
    """Testa todo el flujo de UC"""
    
    # Obtener último proceso
    ultimo_proceso = ProcesoEstructura.objects.filter(
        estado__in=['COMPLETADO', 'CLASIFICADO']
    ).order_by('-created_at').first()
    
    if not ultimo_proceso:
        print("No hay procesos para probar")
        return
    
    print(f"=== PROBANDO PROCESO {ultimo_proceso.id} ===")
    
    if ultimo_proceso.datos_excel:
        print("\n--- DATOS EXCEL BRUTOS (primer registro) ---")
        primer_registro = ultimo_proceso.datos_excel[0]
        
        # Buscar UC en cualquier campo
        uc_encontrado = None
        for campo, valor in primer_registro.items():
            if 'UC' in campo or 'Unidad' in campo or 'Unnamed: 25' in campo:
                print(f"  {campo}: {valor}")
                if 'Unnamed: 25' in campo or 'UC' in campo:
                    uc_encontrado = valor
        
        print(f"\nUC encontrado en datos_excel: {uc_encontrado}")
        
        # Aplicar transformación manual para verificar
        from estructuras.services import DataTransformer
        transformador = DataTransformer('EXPANSION')
        
        registro_normalizado = transformador._normalizar_nombres_campos(primer_registro)
        uc_normalizado = registro_normalizado.get('UC', 'NO_ENCONTRADO')
        print(f"UC después de normalización: {uc_normalizado}")
        
        # Verificar clasificador
        if uc_normalizado != 'NO_ENCONTRADO':
            clasificador = transformador.clasificador
            tipo_proyecto = clasificador._generar_tipo_proyecto_desde_nivel_tension(uc_normalizado)
            print(f"TIPO_PROYECTO generado desde UC '{uc_normalizado}': {tipo_proyecto}")
        
    if ultimo_proceso.datos_norma:
        print("\n--- DATOS NORMA (primer registro) ---")
        primer_norma = ultimo_proceso.datos_norma[0]
        uc_norma = primer_norma.get('UC', 'NO_ENCONTRADO')
        tipo_proyecto_norma = primer_norma.get('TIPO_PROYECTO', 'NO_ENCONTRADO')
        print(f"UC en datos_norma: {uc_norma}")
        print(f"TIPO_PROYECTO en datos_norma: {tipo_proyecto_norma}")

if __name__ == "__main__":
    test_flujo_uc()
