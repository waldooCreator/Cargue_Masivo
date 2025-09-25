#!/usr/bin/env python
"""
Script para probar las mejoras en la configuración Oracle
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.services import OracleHelper
from django.conf import settings

def test_oracle_improvements():
    """Prueba las mejoras en Oracle"""
    print("=== PRUEBA DE MEJORAS ORACLE ===")
    
    # Mostrar configuración
    print(f"Oracle habilitado: {getattr(settings, 'ORACLE_ENABLED', True)}")
    print(f"Timeout configurado: {getattr(settings, 'ORACLE_CONNECTION_TIMEOUT', 10)} segundos")
    print()
    
    # Probar consulta con FID de ejemplo
    test_fids = ["38141915", "38142268", "37591015"]
    
    print("Probando consultas Oracle con timeouts mejorados...")
    for fid in test_fids:
        print(f"\n🔍 Consultando FID: {fid}")
        lat, lon = OracleHelper.obtener_coordenadas_por_fid(fid)
        if lat and lon:
            print(f"   ✅ Resultado: lat={lat}, lon={lon}")
        else:
            print(f"   ⚠️ Sin coordenadas (esperado por timeout/conexión)")

if __name__ == "__main__":
    test_oracle_improvements()