#!/usr/bin/env python
"""
Script de prueba para verificar la integración Oracle en TXT Baja
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.services import OracleHelper

def test_oracle_connection():
    """Prueba la conexión básica a Oracle"""
    print("=== PRUEBA DE CONEXIÓN ORACLE ===")
    
    # 1. Probar conexión básica
    print("1. Probando conexión básica...")
    if OracleHelper.test_connection():
        print("✅ Conexión básica exitosa")
    else:
        print("❌ Error en conexión básica - revisar credenciales")
        print("   Credenciales actuales:")
        print("   Usuario: CENS_CONSULTA")
        print("   Contraseña: C3N5C0N5ULT4")
        print("   Host: EPM-PO18:1521/GENESTB")
        print("   Nota: Verificar que las credenciales sean correctas")
        return False
    
    # 2. Probar con el FID de ejemplo de la imagen: 38142268
    fid_test = "38142268"
    print(f"2. Probando consulta Oracle con FID: {fid_test}")
    
    try:
        lat, lon = OracleHelper.obtener_coordenadas_por_fid(fid_test)
        print(f"   Resultado: lat={lat}, lon={lon}")
        
        if lat and lon:
            print("✅ Consulta EXITOSA - Se obtuvieron coordenadas desde Oracle")
            return True
        else:
            print("⚠️  Consulta exitosa pero no se encontró el FID en la tabla ccomun")
            print("   Esto puede ser normal si el FID no existe en la BD")
            return True
    except Exception as e:
        print(f"❌ Error en consulta Oracle: {str(e)}")
        return False

if __name__ == "__main__":
    test_oracle_connection()