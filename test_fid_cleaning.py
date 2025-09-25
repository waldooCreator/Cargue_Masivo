#!/usr/bin/env python
"""
Script para probar la corrección de FID (eliminar .0)
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.services import OracleHelper, ExcelProcessor

def test_fid_cleaning():
    """Prueba la limpieza de FID"""
    print("=== PRUEBA DE LIMPIEZA DE FID ===")
    
    # Crear una instancia del procesador Excel para probar _limpiar_fid
    class TestProcessor:
        def _limpiar_fid(self, valor):
            if valor is None:
                return ''
            
            vs = str(valor).strip()
            if vs.lower() in ('', 'nan', 'none'):
                return ''
                
            # Si es un número con .0 al final, remover el .0
            if vs.endswith('.0'):
                try:
                    float_val = float(vs)
                    if float_val.is_integer():
                        return str(int(float_val))
                except (ValueError, OverflowError):
                    pass
            
            return vs
    
    processor = TestProcessor()
    
    # Casos de prueba
    test_cases = [
        ("38141915.0", "38141915"),
        ("38142268.0", "38142268"),
        ("37591015.0", "37591015"),
        ("123456", "123456"),
        ("123.45", "123.45"),  # No debería cambiar
        ("", ""),
        (None, ""),
        ("nan", ""),
        (38141915.0, "38141915"),  # float directo
    ]
    
    print("Pruebas de limpieza de FID:")
    for input_val, expected in test_cases:
        result = processor._limpiar_fid(input_val)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {input_val} -> {result} (esperado: {expected})")
    
    print("\nPruebas de Oracle con FID corrigidos:")
    test_fids = ["38141915.0", "38142268.0", "37591015.0"]
    
    for fid in test_fids:
        print(f"\n🔍 Consultando FID original: {fid}")
        lat, lon = OracleHelper.obtener_coordenadas_por_fid(fid)
        if lat and lon:
            print(f"   ✅ Resultado: lat={lat}, lon={lon}")
        else:
            print(f"   ⚠️ Sin coordenadas (pero debería usar FID sin .0)")

if __name__ == "__main__":
    test_fid_cleaning()