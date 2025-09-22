#!/usr/bin/env python3
"""
Test para verificar que los propietarios se carguen correctamente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.constants import REGLAS_CLASIFICACION

def main():
    print("🔍 VERIFICACIÓN DE PROPIETARIOS")
    print("=" * 40)
    
    propietarios_config = REGLAS_CLASIFICACION.get('PROPIETARIOS_VALIDOS', {})
    
    print(f"📊 Configuración de propietarios encontrada:")
    print(f"   - VALORES_ACEPTADOS: {propietarios_config.get('VALORES_ACEPTADOS', [])}")
    print(f"   - VALOR_DEFECTO: {propietarios_config.get('VALOR_DEFECTO', 'N/A')}")
    print(f"   - NORMALIZACION: {len(propietarios_config.get('NORMALIZACION', {}))} reglas")
    
    # Test de acceso como se usa en views.py
    propietarios_predefinidos = REGLAS_CLASIFICACION.get('PROPIETARIOS_VALIDOS', {}).get('VALORES_ACEPTADOS', [])
    print(f"\n✅ Propietarios para la interfaz: {propietarios_predefinidos}")
    print(f"✅ Total: {len(propietarios_predefinidos)} propietarios disponibles")

if __name__ == '__main__':
    main()
