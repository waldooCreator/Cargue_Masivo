from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.conf import settings
import json
import threading
import os
import pandas as pd
from .models import ProcesoEstructura
from .constants import CIRCUITOS_DISPONIBLES_LISTA, REGLAS_CLASIFICACION
from .clasificador import ClasificadorAutomatico

def index(request):
    """Página principal - listado de procesos"""
    # Paginación: mostrar solo los primeros 10 procesos
    procesos = ProcesoEstructura.objects.all().order_by('-created_at')[:10]
    total_procesos = ProcesoEstructura.objects.count()
    
    context = {
        'procesos': procesos,
        'total_procesos': total_procesos,
        'mostrar_ver_mas': total_procesos > 10,
    }
    return render(request, 'estructuras/index.html', context)

@csrf_exempt
@require_http_methods(["GET"])
def cargar_mas_procesos(request):
    """Cargar más procesos para paginación AJAX"""
    try:
        offset = int(request.GET.get('offset', 0))
        limit = 10
        
        procesos = ProcesoEstructura.objects.all().order_by('-created_at')[offset:offset + limit]
        total_procesos = ProcesoEstructura.objects.count()
        
        procesos_data = []
        for proceso in procesos:
            procesos_data.append({
                'id': str(proceso.id),
                'created_at': proceso.created_at.strftime("%d/%m/%Y %H:%M"),
                'tipo_estructura_display': proceso.get_tipo_estructura_display(),
                'estado': proceso.estado,
                'estado_display': proceso.get_estado_display(),
                'progreso_porcentaje': proceso.progreso_porcentaje,
                'detalle_url': f"/proceso/{proceso.id}/"
            })
        
        return JsonResponse({
            'procesos': procesos_data,
            'has_more': offset + limit < total_procesos,
            'next_offset': offset + limit
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def iniciar_proceso(request):
    """Inicia nuevo proceso de carga con clasificación automática"""
    try:
        archivo = request.FILES.get('archivo')
        
        if not archivo:
            return JsonResponse({
                'error': 'Archivo Excel es requerido'
            }, status=400)
        
        # Validar extensión del archivo
        if not archivo.name.lower().endswith(('.xlsx', '.xls')):
            return JsonResponse({
                'error': 'Solo se permiten archivos Excel (.xlsx, .xls)'
            }, status=400)
        
        # Crear proceso
        with transaction.atomic():
            proceso = ProcesoEstructura.objects.create(
                archivo_excel=archivo,
                estado='INICIADO'
            )
        
        # Iniciar clasificación automática en hilo separado
        def clasificar_async():
            try:
                # Actualizar estado
                proceso.estado = 'CLASIFICANDO'
                proceso.save()
                
                # Leer archivo Excel
                df = pd.read_excel(proceso.archivo_excel.path)
                proceso.registros_totales = len(df)
                proceso.save()
                
                # Clasificar automáticamente
                clasificador = ClasificadorAutomatico()
                resultados = clasificador.clasificar_dataset(df)
                
                # Guardar resultados de clasificación (serializable)
                proceso.clasificacion_automatica = {
                    tipo: [
                        {
                            'tipo': r.tipo,
                            'tipo_inversion': r.tipo_inversion,
                            'fid_anterior': r.fid_anterior,
                            'datos': {k: str(v) if pd.notna(v) else '' for k, v in r.datos.items()},
                            'indice': r.indice
                        }
                        for r in lista
                    ] 
                    for tipo, lista in resultados.items()
                }
                
                # Actualizar totales
                proceso.total_expansion = len(resultados['EXPANSION'])
                proceso.total_reposicion_nuevo = len(resultados['REPOSICION_NUEVO'])
                proceso.total_reposicion_bajo = len(resultados['REPOSICION_BAJO'])
                proceso.total_desmantelado = 0  # Unified into REPOSICION_BAJO
                
                # IMPORTANTE: No dejar en CLASIFICADO, continuar el flujo automáticamente
                proceso.estado = 'PROCESANDO'
                proceso.clasificacion_confirmada = True  # Auto-confirmar clasificación
                proceso.save()
                
                # Continuar con el procesamiento automáticamente
                from .services import procesar_estructura_completo
                procesar_estructura_completo(str(proceso.id))
                
            except Exception as e:
                proceso.estado = 'ERROR'
                proceso.errores = [f"Error en clasificación: {str(e)}"]
                proceso.save()
                import traceback
                print(f"Error completo en clasificación: {traceback.format_exc()}")
        
        # Ejecutar clasificación en hilo separado
        thread = threading.Thread(target=clasificar_async)
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'success': True,
            'proceso_id': str(proceso.id),
            'mensaje': 'Proceso iniciado. Clasificando estructuras automáticamente...',
            'redirect_url': reverse('estructuras:proceso_detalle', kwargs={'proceso_id': proceso.id})
        })
        
    except Exception as e:
        import traceback
        print(f"Error en iniciar_proceso: {traceback.format_exc()}")
        return JsonResponse({
            'error': f'Error interno: {str(e)}'
        }, status=500)

def proceso_detalle(request, proceso_id):
    """Vista detalle de un proceso"""
    proceso = get_object_or_404(ProcesoEstructura, id=proceso_id)
    
    # Si el proceso está en estado CLASIFICADO, auto-continuar el procesamiento
    if proceso.estado == 'CLASIFICADO':
        print(f"Proceso {proceso_id} en estado CLASIFICADO, continuando automáticamente...")
        proceso.clasificacion_confirmada = True
        proceso.estado = 'PROCESANDO'
        proceso.save()
        
        # Iniciar procesamiento en hilo separado
        from .services import procesar_estructura_completo
        import threading
        thread = threading.Thread(
            target=procesar_estructura_completo, 
            args=(str(proceso.id),)
        )
        thread.daemon = True
        thread.start()
    
    # Verificar si necesita definir propietario y estado de salud
    propietarios_info = None
    campos_requeridos = {'propietario': False, 'estado_salud': False}
    
    if proceso.estado == 'COMPLETANDO_DATOS' and proceso.datos_norma:
        from .services import ClasificadorEstructuras
        clasificador = ClasificadorEstructuras()
        
        # Verificar propietarios
        propietarios_info = clasificador.verificar_propietarios_en_excel(proceso.datos_norma)
        
        # Usar el nuevo método para verificar campos requeridos
        campos_requeridos = clasificador.verificar_y_marcar_campos_requeridos(proceso)
        
        # Marcar si requiere definir propietario (mantener lógica existente)
        if not propietarios_info['tiene_propietarios'] and not proceso.propietario_definido:
            proceso.requiere_definir_propietario = True
            proceso.save()
    else:
        # Para procesos en otros estados, verificar si requieren estado de salud
        if hasattr(proceso, 'estado_salud_definido') and (not proceso.estado_salud_definido or proceso.estado_salud_definido == 'None'):
            if proceso.datos_excel:
                for registro in proceso.datos_excel:
                    if not registro.get('ESTADO_SALUD') or registro.get('ESTADO_SALUD').strip() == '':
                        campos_requeridos['estado_salud'] = True
                        break
    
    # Importar propietarios predefinidos y opciones de estado de salud
    from .constants import REGLAS_CLASIFICACION, OPCIONES_ESTADO_SALUD
    propietarios_predefinidos = REGLAS_CLASIFICACION.get('PROPIETARIOS_VALIDOS', {}).get('VALORES_ACEPTADOS', [])
    
    context = {
        'proceso': proceso,
        'circuitos_disponibles': CIRCUITOS_DISPONIBLES_LISTA,
        'propietarios_info': propietarios_info,
        'propietarios_predefinidos': propietarios_predefinidos,
        'opciones_estado_salud': OPCIONES_ESTADO_SALUD,
        'campos_requeridos': campos_requeridos,
        'should_auto_update': proceso.estado in ['INICIADO', 'CLASIFICANDO', 'PROCESANDO', 'GENERANDO_ARCHIVOS']
    }
    return render(request, 'estructuras/proceso_detalle.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def completar_campos(request, proceso_id):
    """Completa campos faltantes y genera archivos"""
    proceso = get_object_or_404(ProcesoEstructura, id=proceso_id)
    
    try:
        data = json.loads(request.body)
        campos = data.get('campos', {})
        propietario = data.get('propietario')  # Manejar propietario directamente
        estado_salud = data.get('estado_salud')  # Manejar estado de salud
        estado_estructura = data.get('estado_estructura')  # Nuevo: manejar estado de estructura
        
        with transaction.atomic():
            # Manejar selección de propietario
            if propietario:
                from .services import ClasificadorEstructuras
                clasificador = ClasificadorEstructuras()
                clasificador.aplicar_propietario_a_proceso(proceso, propietario)
                proceso.requiere_definir_propietario = False
                print(f"Propietario '{propietario}' aplicado al proceso {proceso_id}")
            
            # Manejar estado de salud definido por el usuario
            if estado_salud:
                estados_validos = ['BUENO', 'REGULAR', 'MALO']
                if estado_salud in estados_validos:
                    proceso.estado_salud_definido = estado_salud
                    print(f"Estado de salud '{estado_salud}' aplicado al proceso {proceso_id}")
                else:
                    raise ValueError(f"Estado de salud inválido: {estado_salud}")
            
            # Manejar estado de estructura definido por el usuario
            if estado_estructura:
                estados_validos = REGLAS_CLASIFICACION.get('ESTADOS_DISPONIBLES', ['CONSTRUCCION', 'RETIRADO', 'OPERACION'])
                if estado_estructura in estados_validos:
                    proceso.estado_estructura_definido = estado_estructura
                    print(f"Estado de estructura '{estado_estructura}' aplicado al proceso {proceso_id}")
                else:
                    raise ValueError(f"Estado de estructura inválido: {estado_estructura}")
            
            # Actualizar circuito en el proceso
            if 'CIRCUITO' in campos:
                proceso.circuito = campos['CIRCUITO']
                print(f"Circuito '{campos['CIRCUITO']}' actualizado en proceso {proceso_id}")
            
            # Si hay campos para actualizar
            if campos:
                # Combinar datos_excel con datos_norma para tener toda la información
                datos_norma_actualizados = []
                for i, registro_norma in enumerate(proceso.datos_norma):
                    # Empezar con el registro de datos_excel correspondiente
                    if i < len(proceso.datos_excel):
                        registro_actualizado = proceso.datos_excel[i].copy()
                        
                        # Sobrescribir con valores de datos_norma (campos procesados)
                        registro_actualizado.update(registro_norma)
                        
                        # Aplicar nuevos campos del formulario
                        for campo, valor in campos.items():
                            registro_actualizado[campo] = valor
                        
                        # Si se definió propietario, aplicarlo a todos los registros
                        if proceso.propietario_definido:
                            registro_actualizado['PROPIETARIO'] = proceso.propietario_definido
                    else:
                        # Fallback si no hay datos_excel correspondientes
                        registro_actualizado = registro_norma.copy()
                        for campo, valor in campos.items():
                            registro_actualizado[campo] = valor
                        
                        if proceso.propietario_definido:
                            registro_actualizado['PROPIETARIO'] = proceso.propietario_definido
                    
                    datos_norma_actualizados.append(registro_actualizado)
                
                # Aplicar clasificador para actualizar tipos de estructura
                try:
                    clasificador = ClasificadorEstructuras()
                    datos_clasificados = []
                    for registro in datos_norma_actualizados:
                        registro_clasificado = clasificador.clasificar_estructura(registro)
                        
                        # IMPORTANTE: Asegurar que el propietario seleccionado se mantenga después de la clasificación
                        if proceso.propietario_definido:
                            registro_clasificado['PROPIETARIO'] = proceso.propietario_definido
                            registro_clasificado['PORCENTAJE_PROPIEDAD'] = '100'
                        
                        datos_clasificados.append(registro_clasificado)
                    
                    proceso.datos_norma = datos_clasificados
                    
                    # Obtener y guardar estadísticas de clasificación
                    estadisticas = clasificador.obtener_estadisticas(datos_clasificados)
                    proceso.estadisticas_clasificacion = estadisticas
                    
                except Exception as e:
                    # Continuar sin clasificación si hay error
                    proceso.datos_norma = datos_norma_actualizados
                    proceso.estadisticas_clasificacion = {}  # Usar dict vacío en lugar de None
                    print(f"Error en clasificación: {str(e)}")
            
            # Verificar si aún quedan datos por completar
            campos_pendientes = {}
            
            # Verificar circuito
            if not proceso.circuito:
                campos_pendientes['circuito'] = True
                print(f"Circuito faltante en proceso {proceso_id}")
            
            # Verificar propietario
            if proceso.requiere_definir_propietario:
                campos_pendientes['propietario'] = True
                print(f"Propietario faltante en proceso {proceso_id}")
            
            # Verificar estado de salud
            if not proceso.estado_salud_definido or proceso.estado_salud_definido == 'None':
                # Verificar si hay registros con ESTADO_SALUD vacío
                estado_salud_vacio = False
                if proceso.datos_excel:
                    for registro in proceso.datos_excel:
                        if not registro.get('ESTADO_SALUD') or registro.get('ESTADO_SALUD').strip() == '':
                            estado_salud_vacio = True
                            break
                
                if estado_salud_vacio:
                    campos_pendientes['estado_salud'] = True
                    print(f"Estado de salud faltante en proceso {proceso_id}")
            
            # Verificar campos faltantes - si procesamos campos, limpiar campos_faltantes
            if campos:
                proceso.campos_faltantes = {}  # Limpiar campos faltantes después de procesarlos
            
            if proceso.campos_faltantes:
                campos_pendientes['campos_adicionales'] = True
                print(f"Campos adicionales faltantes en proceso {proceso_id}: {proceso.campos_faltantes}")
            
            print(f"Campos pendientes para proceso {proceso_id}: {campos_pendientes}")
            
            # Si no hay campos pendientes, proceder a generar archivos
            if not campos_pendientes:
                proceso.campos_faltantes = {}  # Ya no hay campos faltantes
                proceso.estado = 'GENERANDO_ARCHIVOS'
                proceso.save()
                
                print(f"Generando archivos para proceso {proceso_id}")
                
                # Generar archivos
                try:
                    from .services import FileGenerator
                    generator = FileGenerator(proceso)
                    
                    # Generar archivos TXT y XML por separado
                    archivo_txt = None
                    try:
                        archivo_txt = generator.generar_txt()
                    except Exception as e:
                        # Si el servicio acumuló errores estructurados, devolverlos en JSON
                        if proceso.errores and isinstance(proceso.errores, list) and proceso.errores and isinstance(proceso.errores[0], dict):
                            return JsonResponse({'success': False, 'errores': proceso.errores}, status=400)
                        # Caso contrario, devolver mensaje plano
                        from django.http import HttpResponse
                        return HttpResponse(str(e), status=400, content_type='text/plain; charset=utf-8')
                    
                    archivo_xml = generator.generar_xml()
                    
                    # Intentar generar archivos de baja
                    archivo_txt_baja = None
                    try:
                        archivo_txt_baja = generator.generar_txt_baja()
                        print(f"Archivo TXT de baja generado correctamente: {archivo_txt_baja}")
                    except Exception as e:
                        print(f"Error generando txt_baja: {e}")

                    archivo_xml_baja = None
                    try:
                        archivo_xml_baja = generator.generar_xml_baja()
                        print(f"Archivo XML de baja generado correctamente: {archivo_xml_baja}")
                    except Exception as e:
                        print(f"Error generando xml_baja: {e}")

                    # Preparar lista de archivos generados
                    archivos = {
                        'txt': archivo_txt,
                        'xml': archivo_xml,
                    }
                    
                    # Agregar archivos de baja solo si se generaron exitosamente
                    if archivo_txt_baja:
                        archivos['txt_baja'] = archivo_txt_baja
                    if archivo_xml_baja:
                        archivos['xml_baja'] = archivo_xml_baja
                    
                    print(f"Archivos generados: {archivos}")
                    
                    proceso.archivos_generados = archivos
                    proceso.estado = 'COMPLETADO'
                    proceso.save()
                    
                    print(f"Proceso {proceso_id} completado exitosamente")
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Proceso completado exitosamente',
                        'estado': 'COMPLETADO',
                        'archivos': archivos
                    })
                    
                except Exception as e:
                    print(f"Error generando archivos: {str(e)}")
                    proceso.estado = 'ERROR'
                    proceso.errores = [f"Error generando archivos: {str(e)}"]
                    proceso.save()
                    # Responder con texto plano; si proviene de generar_txt ya viene normalizado
                    from django.http import HttpResponse
                    return HttpResponse(str(e), status=400, content_type='text/plain; charset=utf-8')
            else:
                # Aún hay campos pendientes, guardar progreso
                proceso.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Datos guardados correctamente',
                    'campos_pendientes': campos_pendientes
                })
                
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def estado_proceso(request, proceso_id):
    """API para obtener estado del proceso"""
    proceso = get_object_or_404(ProcesoEstructura, id=proceso_id)
    
    return JsonResponse({
        'estado': proceso.estado,
        'progreso': proceso.progreso_porcentaje,
        'registros_totales': proceso.registros_totales,
        'registros_procesados': proceso.registros_procesados,
        'tiene_errores': proceso.errores != [],
        'errores': proceso.errores,
    })


@require_http_methods(["GET"])
def estadisticas_clasificacion(request, proceso_id):
    """API para obtener estadísticas de clasificación"""
    proceso = get_object_or_404(ProcesoEstructura, id=proceso_id)
    
    return JsonResponse({
        'estadisticas': proceso.estadisticas_clasificacion or {},
        'tiene_estadisticas': bool(proceso.estadisticas_clasificacion)
    })

@require_http_methods(["GET"])
def descargar_archivo(request, proceso_id, tipo_archivo):
    """Descarga archivo generado (txt, xml, norma_txt, norma_xml, txt_baja, xml_baja, txt_linea, xml_linea)"""
    proceso = get_object_or_404(ProcesoEstructura, id=proceso_id)
    
    if not proceso.archivos_generados:
        raise Http404("No hay archivos generados para este proceso")

    if tipo_archivo not in ['txt', 'xml', 'norma_txt', 'norma_xml', 'txt_baja', 'xml_baja', 'txt_linea', 'xml_linea']:
        raise Http404("Tipo de archivo no válido")

    # Definir nombres de descarga fijos y descriptivos sin cambiar los nombres físicos
    nombres_descarga = {
        'txt': 'estructuras_txt_nuevo.txt',
        'xml': 'estructuras_xml_nuevo.xml',
        'norma_txt': 'estructuras_txt_norma.txt',
        'norma_xml': 'estructuras_xml_norma.xml',
        'txt_baja': 'estructuras_txt_baja.txt',
        'xml_baja': 'estructuras_xml_baja.xml',
        'txt_linea': 'conductores_txt_linea.txt',
        'xml_linea': 'conductores_xml_linea.xml',
    }
    
    # Manejo especial para txt_baja
    if tipo_archivo == 'txt_baja':
        # Verificar si ya está registrado en archivos_generados
        if 'txt_baja' in proceso.archivos_generados:
            # Usar el archivo registrado
            filename = proceso.archivos_generados['txt_baja']
            filepath = os.path.join(settings.MEDIA_ROOT, 'generated', filename)
            
            if os.path.exists(filepath):
                response = FileResponse(
                    open(filepath, 'rb'),
                    as_attachment=True,
                    filename=nombres_descarga.get('txt_baja', filename)
                )
                return response
        
        # Si no está registrado o no existe, generar dinámicamente
        try:
            from .services import FileGenerator
            generator = FileGenerator(proceso)
            
            # Generar archivo TXT baja
            filename_generated = generator.generar_txt_baja()
            generated_filepath = os.path.join(settings.MEDIA_ROOT, 'generated', filename_generated)
            
            # Registrar en base de datos
            if not proceso.archivos_generados:
                proceso.archivos_generados = {}
            proceso.archivos_generados['txt_baja'] = filename_generated
            proceso.save()
            
            # Servir archivo recién generado
            response = FileResponse(
                open(generated_filepath, 'rb'),
                as_attachment=True,
                filename=nombres_descarga.get('txt_baja', filename_generated)
            )
            return response
            
        except Exception as e:
            print(f"Error generando TXT baja: {str(e)}")
            raise Http404("Error al generar archivo TXT_BAJA")

    # Manejo especial para norma_txt
    if tipo_archivo == 'norma_txt':
        if 'norma_txt' in proceso.archivos_generados:
            filename = proceso.archivos_generados['norma_txt']
            filepath = os.path.join(settings.MEDIA_ROOT, 'generated', filename)
            if os.path.exists(filepath):
                return FileResponse(open(filepath, 'rb'), as_attachment=True, filename=nombres_descarga.get('norma_txt', filename))
        try:
            from .services import FileGenerator
            generator = FileGenerator(proceso)
            filename_generated = generator.generar_norma_txt()
            generated_filepath = os.path.join(settings.MEDIA_ROOT, 'generated', filename_generated)
            if not proceso.archivos_generados:
                proceso.archivos_generados = {}
            proceso.archivos_generados['norma_txt'] = filename_generated
            proceso.save()
            return FileResponse(open(generated_filepath, 'rb'), as_attachment=True, filename=nombres_descarga.get('norma_txt', filename_generated))
        except Exception as e:
            print(f"Error generando norma TXT: {str(e)}")
            raise Http404("Error al generar archivo NORMA_TXT")

    # Manejo especial para norma_xml
    if tipo_archivo == 'norma_xml':
        if 'norma_xml' in proceso.archivos_generados:
            filename = proceso.archivos_generados['norma_xml']
            filepath = os.path.join(settings.MEDIA_ROOT, 'generated', filename)
            if os.path.exists(filepath):
                return FileResponse(open(filepath, 'rb'), as_attachment=True, filename=nombres_descarga.get('norma_xml', filename))
        try:
            from .services import FileGenerator
            generator = FileGenerator(proceso)
            filename_generated = generator.generar_norma_xml()
            generated_filepath = os.path.join(settings.MEDIA_ROOT, 'generated', filename_generated)
            if not proceso.archivos_generados:
                proceso.archivos_generados = {}
            proceso.archivos_generados['norma_xml'] = filename_generated
            proceso.save()
            return FileResponse(open(generated_filepath, 'rb'), as_attachment=True, filename=nombres_descarga.get('norma_xml', filename_generated))
        except Exception as e:
            print(f"Error generando norma XML: {str(e)}")
            raise Http404("Error al generar archivo NORMA_XML")
    
    # Manejo especial para txt_linea (CONDUCTORES)
    if tipo_archivo == 'txt_linea':
        # Por ahora retornamos un archivo placeholder hasta implementar la lógica real
        raise Http404("TXT Línea: Funcionalidad en desarrollo")
    
    # Manejo especial para xml_linea (CONDUCTORES)
    if tipo_archivo == 'xml_linea':
        # Por ahora retornamos un archivo placeholder hasta implementar la lógica real
        raise Http404("XML Línea: Funcionalidad en desarrollo")
    
    # Manejo normal para otros tipos de archivo
    filename = proceso.archivos_generados.get(tipo_archivo)
    if not filename:
        raise Http404(f"Archivo {tipo_archivo.upper()} no encontrado")
    
    filepath = os.path.join(settings.MEDIA_ROOT, 'generated', filename)
    
    if not os.path.exists(filepath):
        raise Http404("Archivo no encontrado en el sistema")
    
    response = FileResponse(
        open(filepath, 'rb'),
        as_attachment=True,
        filename=nombres_descarga.get(tipo_archivo, filename)
    )
    return response


# ==========================================
# VISTAS DE CLASIFICACIÓN AUTOMÁTICA
# ==========================================

@csrf_exempt
def revisar_clasificacion(request, proceso_id):
    """Vista para revisar y ajustar la clasificación automática"""
    proceso = get_object_or_404(ProcesoEstructura, id=proceso_id)
    
    if request.method == 'GET':
        # Mostrar página de revisión
        if not proceso.clasificacion_automatica:
            messages.error(request, 'El proceso no tiene clasificación automática disponible')
            return redirect('estructuras:proceso_detalle', proceso_id=proceso_id)
        
        # Preparar resumen para mostrar
        resumen = {
            'proceso_id': str(proceso.id),
            'total_registros': proceso.registros_totales,
            'expansion': {
                'cantidad': proceso.total_expansion,
                'registros': proceso.clasificacion_automatica.get('EXPANSION', [])[:10]  # Primeros 10
            },
            'reposicion_nuevo': {
                'cantidad': proceso.total_reposicion_nuevo,
                'registros': proceso.clasificacion_automatica.get('REPOSICION_NUEVO', [])[:10]
            },
            'reposicion_bajo': {
                'cantidad': proceso.total_reposicion_bajo,
                'registros': proceso.clasificacion_automatica.get('REPOSICION_BAJO', [])[:10]
            },
            'desmantelado': {
                'cantidad': proceso.total_desmantelado,
                'registros': proceso.clasificacion_automatica.get('DESMANTELADO', [])[:10]
            }
        }
        
        context = {
            'proceso': proceso,
            'resumen': resumen
        }
        return render(request, 'estructuras/revisar_clasificacion.html', context)
    
    elif request.method == 'POST':
        # Procesar ajustes manuales
        try:
            data = json.loads(request.body)
            ajustes = data.get('ajustes', [])
            confirmar = data.get('confirmar', False)
            
            if ajustes:
                # Guardar ajustes manuales
                proceso.ajustes_clasificacion = ajustes
                
                # Aplicar ajustes a la clasificación
                # TODO: Implementar lógica para aplicar ajustes
                
            if confirmar:
                # Confirmar clasificación y continuar con el flujo normal
                proceso.clasificacion_confirmada = True
                proceso.estado = 'COMPLETANDO_DATOS'  # Cambiar a COMPLETANDO_DATOS para continuar el flujo
                proceso.save()
                
                return JsonResponse({
                    'success': True,
                    'mensaje': 'Clasificación confirmada. Redirigiendo para completar datos...',
                    'redirect_url': reverse('estructuras:proceso_detalle', kwargs={'proceso_id': proceso.id})
                })
            else:
                proceso.save()
                return JsonResponse({
                    'success': True,
                    'mensaje': 'Ajustes guardados correctamente'
                })
                
        except Exception as e:
            return JsonResponse({
                'error': f'Error procesando ajustes: {str(e)}'
            }, status=500)


@csrf_exempt  
def obtener_estado_clasificacion(request, proceso_id):
    """API para obtener el estado actual de la clasificación"""
    proceso = get_object_or_404(ProcesoEstructura, id=proceso_id)
    
    return JsonResponse({
        'estado': proceso.estado,
        'clasificacion_confirmada': proceso.clasificacion_confirmada,
        'total_registros': proceso.registros_totales,
        'total_expansion': proceso.total_expansion,
        'total_reposicion_nuevo': proceso.total_reposicion_nuevo,
        'total_reposicion_bajo': proceso.total_reposicion_bajo,
        'total_desmantelado': proceso.total_desmantelado,
        'errores': proceso.errores if proceso.errores else []
    })
