#!/usr/bin/env python
"""
Script para probar la configuración de Oracle después de los cambios
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.services import OracleHelper

def test_oracle_config():
    """Prueba la configuración de Oracle"""
    print("=== PRUEBA DE CONFIGURACIÓN ORACLE ===")
    
    # Obtener configuración
    config = OracleHelper.get_oracle_config()
    print(f"Configuración Oracle:")
    print(f"  Usuario: {config['user']}")
    print(f"  DSN: {config['dsn']}")
    print(f"  Password: {'*' * len(config['password'])}")
    print()
    
    # Probar conexión
    print("Probando conexión a Oracle...")
    if OracleHelper.test_connection():
        print("✅ Conexión exitosa!")
    else:
        print("❌ Error en la conexión")
    print()
    
    # Probar consulta de coordenadas
    print("Probando consulta de coordenadas por FID...")
    test_fid = "12345"  # FID de prueba
    lat, lon = OracleHelper.obtener_coordenadas_por_fid(test_fid)
    print(f"FID {test_fid}: lat={lat}, lon={lon}")

if __name__ == "__main__":
    test_oracle_config()