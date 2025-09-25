#!/usr/bin/env python
"""
Script para mostrar la consulta SQL exacta que se ejecuta
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

def test_sql_query():
    """Muestra la consulta SQL que se ejecutará"""
    print("=== CONSULTA SQL QUE SE EJECUTARÁ ===")
    
    test_fids = ["38141915.0", "38142268.0", "37591015.0"]
    
    for fid_original in test_fids:
        # Simular la limpieza de FID
        fid_limpio = fid_original
        if fid_limpio.endswith('.0'):
            try:
                float_val = float(fid_limpio)
                if float_val.is_integer():
                    fid_limpio = str(int(float_val))
            except (ValueError, OverflowError):
                pass
        
        print(f"\n🔍 FID original: {fid_original}")
        print(f"   FID limpio: {fid_limpio}")
        print(f"   Consulta SQL:")
        print(f"   SELECT g3e_fid, coor_gps_lat, coor_gps_lon")
        print(f"   FROM ccomun c")
        print(f"   WHERE g3e_fid = {fid_limpio}")
        print(f"   -- (parámetro: {fid_limpio})")

if __name__ == "__main__":
    test_sql_query()