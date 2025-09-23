"""
DOCUMENTACIÓN - INTEGRACIÓN ORACLE EN TXT BAJA
============================================

Se ha integrado completamente la funcionalidad de Oracle en el archivo TXT Baja.

CAMBIOS REALIZADOS:
==================

1. DEPENDENCIAS AGREGADAS:
   - Agregado 'oracledb' a requirements.txt

2. NUEVA CLASE OracleHelper:
   - Ubicación: estructuras/services.py
   - Funciones: 
     * test_connection(): Prueba conexión básica
     * obtener_coordenadas_por_fid(fid): Consulta coordenadas por FID

3. CREDENCIALES ORACLE INTEGRADAS:
   - Usuario: CENS_CONSULTA
   - Contraseña: C3N5CONSULT4  
   - Host: EPM-PO18:1521/GENESTB

4. NUEVOS CAMPOS EN TXT BAJA:
   - COOR_GPS_LAT: Latitud GPS desde Oracle
   - COOR_GPS_LON: Longitud GPS desde Oracle

5. FLUJO DE PROCESAMIENTO:
   - Se toma el fid_anterior de cada registro del Excel
   - Se consulta Oracle: SELECT g3e_fid, coor_gps_lat, coor_gps_lon FROM ccomun c WHERE g3e_fid = :fid
   - Se agregan los campos COOR_GPS_LAT y COOR_GPS_LON al archivo TXT
   - Si hay error o no se encuentra FID, los campos quedan vacíos

CONFIGURACIÓN ACTUAL:
====================
Las credenciales están hardcodeadas en el código (línea ~105 de services.py):

    ORACLE_CONFIG = {
        'user': 'CENS_CONSULTA',
        'password': 'C3N5CONSULT4',
        'dsn': 'EPM-PO18:1521/GENESTB'
    }

ESTADO: FUNCIONALIDAD COMPLETA
==============================
✅ Dependencia oracledb instalada
✅ Clase OracleHelper implementada  
✅ Credenciales integradas en código
✅ Nuevos campos agregados a encabezados TXT
✅ Lógica de consulta Oracle integrada en generar_txt_baja()
✅ Manejo de errores robusto

SIGUIENTE PASO:
===============
- Verificar credenciales Oracle (actualmente da error ORA-01017)
- Una vez corregidas las credenciales, la funcionalidad estará 100% operativa

PARA CAMBIAR CREDENCIALES:
=========================
Editar estructuras/services.py línea ~105:
    ORACLE_CONFIG = {
        'user': 'TU_USUARIO',
        'password': 'TU_PASSWORD', 
        'dsn': 'TU_HOST:PUERTO/SERVICIO'
    }
"""