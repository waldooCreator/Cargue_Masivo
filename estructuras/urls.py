from django.urls import path
from . import views

app_name = 'estructuras'

urlpatterns = [
    path('', views.index, name='index'),
    path('iniciar-proceso/', views.iniciar_proceso, name='iniciar_proceso'),
    path('cargar-mas-procesos/', views.cargar_mas_procesos, name='cargar_mas_procesos'),
    path('proceso/<uuid:proceso_id>/', views.proceso_detalle, name='proceso_detalle'),
    path('proceso/<uuid:proceso_id>/estado/', views.estado_proceso, name='estado_proceso'),
    
    # URLs para clasificación automática
    path('proceso/<uuid:proceso_id>/revisar-clasificacion/', views.revisar_clasificacion, name='revisar_clasificacion'),
    path('proceso/<uuid:proceso_id>/estado-clasificacion/', views.obtener_estado_clasificacion, name='obtener_estado_clasificacion'),
    
    # URLs existentes
    path('proceso/<uuid:proceso_id>/completar/', views.completar_campos, name='completar_campos'),
    path('proceso/<uuid:proceso_id>/estadisticas/', views.estadisticas_clasificacion, name='estadisticas_clasificacion'),
    path('proceso/<uuid:proceso_id>/descargar/<str:tipo_archivo>/', views.descargar_archivo, name='descargar_archivo'),
]
