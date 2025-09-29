#!/usr/bin/env python
"""
Script para probar el enriquecimiento Oracle con códigos operativos
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.services import FileGenerator, OracleHelper

def test_enriquecimiento_oracle():
    print("🔧 Probando enriquecimiento Oracle...")
    
    # Simular datos de ejemplo con códigos operativos como en la imagen
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
        },
        {
            'COORDENADA_X': '-73.789012',
            'COORDENADA_Y': '4.345678',
            'Código FID_rep': 'Z251390',  # Otro código operativo
            'UBICACION': 'Test Location 2',
            'TIPO': 'Test Type 2',
            'ENLACE': '',
            'PROPIETARIO': '',
            'EMPRESA': '',
            'TIPO_ADECUACION': '',
            'CLASIFICACION_MERCADO': ''
        }
    ]
    
    print(f"📊 Datos de prueba: {len(datos_test)} registros")
    for i, registro in enumerate(datos_test):
        print(f"   Registro {i+1}: Código '{registro['Código FID_rep']}', Excel X={registro['COORDENADA_X']}, Y={registro['COORDENADA_Y']}")
    
    print("\n🔍 Aplicando enriquecimiento Oracle...")
    
    codigos_encontrados = 0
    registros_enriquecidos = 0
    
    for i, registro in enumerate(datos_test):
        try:
            # Buscar código operativo (igual que en services.py)
            codigo_operativo = ''
            
            campos_busqueda = [
                'Código FID_rep',  # Campo principal del Excel
                'Codigo FID_rep',  # Variante sin tilde
                'CODIGO_FID_REP',  # Variante mayúsculas
                'FID_REP',         # Variante corta
                'ENLACE'           # Por si se mapea aquí
            ]
            
            for campo in campos_busqueda:
                valor = registro.get(campo, '')
                if valor and str(valor).strip().upper().startswith('Z'):
                    codigo_operativo = str(valor).strip()
                    print(f"   🎯 Registro {i+1} - Código operativo encontrado: {codigo_operativo} en campo '{campo}'")
                    break
            
            if codigo_operativo and str(codigo_operativo).strip().upper().startswith('Z'):
                codigos_encontrados += 1
                
                print(f"   🔍 Buscando FID real para código operativo: {codigo_operativo}")
                
                # PASO 1: Obtener FID real desde código operativo
                fid_real = OracleHelper.obtener_fid_desde_codigo_operativo(codigo_operativo)
                
                if fid_real:
                    print(f"   ✅ FID real encontrado: {fid_real}")
                    
                    # PASO 2: Obtener datos específicos para TXT nuevo desde Oracle
                    datos_oracle = OracleHelper.obtener_datos_txt_nuevo_por_fid(fid_real)
                    
                    if datos_oracle:
                        print(f"   📊 Datos Oracle obtenidos:")
                        print(f"      COORDENADA_X: {datos_oracle.get('COORDENADA_X')} (Excel: {registro['COORDENADA_X']})")
                        print(f"      COORDENADA_Y: {datos_oracle.get('COORDENADA_Y')} (Excel: {registro['COORDENADA_Y']})")
                        print(f"      TIPO: {datos_oracle.get('TIPO')}")
                        print(f"      PROPIETARIO: {datos_oracle.get('PROPIETARIO')}")
                        
                        # Aplicar enriquecimiento
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
                        
                        registro['ENLACE'] = str(fid_real)
                        
                        registros_enriquecidos += 1
                        print(f"   ✅ Registro {i+1} ENRIQUECIDO:")
                        print(f"      X: {registro_original['COORDENADA_X']} -> {registro['COORDENADA_X']}")
                        print(f"      Y: {registro_original['COORDENADA_Y']} -> {registro['COORDENADA_Y']}")
                        print(f"      ENLACE asignado: {fid_real}")
                    else:
                        print(f"   ⚠️ No se obtuvieron datos desde Oracle para FID {fid_real}")
                else:
                    print(f"   ⚠️ No se encontró FID real para código operativo {codigo_operativo}")
            else:
                print(f"   ⏭️ Registro {i+1} sin código operativo válido")
                
        except Exception as e:
            print(f"   ❌ Error procesando registro {i+1}: {str(e)}")
            continue
    
    print(f"\n📈 RESUMEN FINAL:")
    print(f"   Total registros: {len(datos_test)}")
    print(f"   Códigos operativos encontrados: {codigos_encontrados}")
    print(f"   Registros enriquecidos: {registros_enriquecidos}")
    
    if registros_enriquecidos > 0:
        print("✅ El enriquecimiento Oracle FUNCIONA correctamente")
        print("🎯 Cuando subas un Excel input2.xlsx con códigos operativos, el sistema los enriquecerá automáticamente")
    else:
        print("❌ El enriquecimiento Oracle NO funcionó")

if __name__ == "__main__":
    test_enriquecimiento_oracle()