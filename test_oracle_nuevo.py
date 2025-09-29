#!/usr/bin/env python
"""
Script para probar el enriquecimiento Oracle TXT NUEVO corregido
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.services import OracleHelper

def test_enriquecimiento_oracle_nuevo():
    print("🔧 Probando enriquecimiento Oracle TXT NUEVO...")
    
    # Simular datos de ejemplo con códigos operativos para TXT NUEVO
    datos_test = [
        {
            'COORDENADA_X': '-73.123456',  # Coordenada del Excel
            'COORDENADA_Y': '4.654321',   # Coordenada del Excel
            'Código FID_rep': 'Z238163',  # Código operativo desde Excel
            'UBICACION': 'Test Location',
            'TIPO': 'Test Type',
            'ENLACE': '',
            'PROPIETARIO': '',
            'EMPRESA': '',
            'TIPO_ADECUACION': '',
            'CLASIFICACION_MERCADO': ''
        }
    ]
    
    print(f"📊 Datos de prueba TXT NUEVO: {len(datos_test)} registros")
    for i, registro in enumerate(datos_test):
        print(f"   Registro {i+1}: Código '{registro['Código FID_rep']}', Excel X={registro['COORDENADA_X']}, Y={registro['COORDENADA_Y']}")
    
    print("\n🔍 Aplicando enriquecimiento Oracle TXT NUEVO...")
    
    # Test del método obtener_datos_txt_nuevo_por_fid
    codigo_operativo = 'Z238163'
    print(f"   🔍 Buscando FID real para código operativo: {codigo_operativo}")
    
    # PASO 1: Obtener FID real desde código operativo
    fid_real = OracleHelper.obtener_fid_desde_codigo_operativo(codigo_operativo)
    
    if fid_real:
        print(f"   ✅ FID real encontrado: {fid_real}")
        
        # PASO 2: Obtener datos específicos para TXT nuevo desde Oracle
        datos_oracle = OracleHelper.obtener_datos_txt_nuevo_por_fid(fid_real)
        
        if datos_oracle:
            print(f"   📊 Datos Oracle TXT NUEVO obtenidos:")
            print(f"      COORDENADA_X: {datos_oracle.get('COORDENADA_X')} (Excel: {datos_test[0]['COORDENADA_X']})")
            print(f"      COORDENADA_Y: {datos_oracle.get('COORDENADA_Y')} (Excel: {datos_test[0]['COORDENADA_Y']})")
            print(f"      TIPO: {datos_oracle.get('TIPO')}")
            print(f"      PROPIETARIO: {datos_oracle.get('PROPIETARIO')}")
            
            # Aplicar enriquecimiento
            registro = datos_test[0]
            registro_original = registro.copy()
            
            if datos_oracle.get('COORDENADA_X'):
                registro['COORDENADA_X'] = datos_oracle['COORDENADA_X']
            if datos_oracle.get('COORDENADA_Y'):
                registro['COORDENADA_Y'] = datos_oracle['COORDENADA_Y']
            if datos_oracle.get('TIPO'):
                registro['TIPO'] = datos_oracle['TIPO']
            if datos_oracle.get('TIPO_ADECUACION'):
                registro['TIPO_ADECUACION'] = datos_oracle['TIPO_ADECUACION']
            if datos_oracle.get('PROPIETARIO'):
                registro['PROPIETARIO'] = datos_oracle['PROPIETARIO']
                registro['EMPRESA'] = datos_oracle['PROPIETARIO']
            if datos_oracle.get('UBICACION'):
                registro['UBICACION'] = datos_oracle['UBICACION']
            if datos_oracle.get('CLASIFICACION_MERCADO'):
                registro['CLASIFICACION_MERCADO'] = datos_oracle['CLASIFICACION_MERCADO']
            
            # FID real
            registro['ENLACE'] = str(fid_real)
            
            print(f"   ✅ Registro TXT NUEVO ENRIQUECIDO:")
            print(f"      X: {registro_original['COORDENADA_X']} -> {registro['COORDENADA_X']}")
            print(f"      Y: {registro_original['COORDENADA_Y']} -> {registro['COORDENADA_Y']}")
            print(f"      ENLACE: {registro['ENLACE']}")
            
            if registro['COORDENADA_X'] != registro_original['COORDENADA_X']:
                print("✅ El enriquecimiento Oracle TXT NUEVO FUNCIONA correctamente")
                print("🎯 Los archivos TXT NUEVO ahora mostrarán coordenadas Oracle (-72.xxx) en lugar de Excel (-73.xxx)")
                
                # Comparar con los datos de TXT BAJA para verificar consistencia
                datos_oracle_baja = OracleHelper.obtener_datos_txt_baja_por_fid(fid_real)
                if datos_oracle_baja:
                    print(f"\n🔄 Verificando consistencia TXT NUEVO vs TXT BAJA:")
                    print(f"   TXT NUEVO - X: {datos_oracle.get('COORDENADA_X')}, Y: {datos_oracle.get('COORDENADA_Y')}")
                    print(f"   TXT BAJA  - X: {datos_oracle_baja.get('COORDENADA_X')}, Y: {datos_oracle_baja.get('COORDENADA_Y')}")
                    
                    if (datos_oracle.get('COORDENADA_X') == datos_oracle_baja.get('COORDENADA_X') and 
                        datos_oracle.get('COORDENADA_Y') == datos_oracle_baja.get('COORDENADA_Y')):
                        print("✅ TXT NUEVO y TXT BAJA son consistentes")
                    else:
                        print("⚠️ Hay diferencias entre TXT NUEVO y TXT BAJA")
            else:
                print("❌ El enriquecimiento Oracle TXT NUEVO NO cambió las coordenadas")
        else:
            print(f"   ⚠️ No se obtuvieron datos desde Oracle para FID {fid_real}")
    else:
        print(f"   ⚠️ No se encontró FID real para código operativo {codigo_operativo}")

if __name__ == "__main__":
    test_enriquecimiento_oracle_nuevo()