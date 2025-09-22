#!/usr/bin/env python3
"""
Test específico para verificar mapeo de UC
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.services import DataTransformer

def test_mapeo_uc():
    """Testa el mapeo específico de UC"""
    
    # Crear instancia del transformador
    transformador = DataTransformer('EXPANSION')
    
    # Simular registro con UC en formato Unnamed
    registro_test = {
        'Unnamed: 0': '-73.24081',
        'Unnamed: 1': '8.257043',  
        'Unnamed: 25': 'N3L75',    # Este es el UC
        'Unnamed: 23': '1',        # Este es el código inventario
        'Nombre del proyecto': 'Test'
    }
    
    print("=== ANTES DE NORMALIZACIÓN ===")
    for campo, valor in registro_test.items():
        print(f"  {campo}: {valor}")
    
    # Aplicar normalización
    registro_normalizado = transformador._normalizar_nombres_campos(registro_test)
    
    print("\n=== DESPUÉS DE NORMALIZACIÓN ===")
    for campo, valor in registro_normalizado.items():
        print(f"  {campo}: {valor}")
    
    # Verificar específicamente UC
    uc_valor = registro_normalizado.get('UC', 'NO_ENCONTRADO')
    print(f"\n=== RESULTADO UC ===")
    print(f"UC extraído: {uc_valor}")
    
    if uc_valor == 'N3L75':
        print("✅ UC se mapeó correctamente")
    else:
        print("❌ UC NO se mapeó correctamente")

if __name__ == "__main__":
    test_mapeo_uc()
