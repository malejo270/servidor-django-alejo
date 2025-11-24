"""
URL configuration for emcali_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from mantenimiento.views import login_view,ini,logout_view,mantenimiento,crear_nodo,crear_comunicacion,crear_reco,crear_subestacion,crear_orden,lista_ordenes,crear_informe_reco,conexion_cascada_view,ordenes_creadas_ingeniero,ver_informe_reco,detalle_nodo_reco_comunicacion,vista_general_recos,reporte_emergencia,historicos_recos,historico_trabajos,editar_nodo_reco_comunicacion,eliminar_comunicacion,vista_general_recos_ope,dashboard_completo,elegir_inge,subestaciones,editar_subestacion,crear_informe_subestacion,ver_informe_sub_comu,subestaciones_comunicacion,historico_sub_comu,mapa_nodos,historicos_recos_pdf,revisar_subestacion,lista_preguntas,crear_pregunta,eliminar_pregunta,subestaciones_operario,seleccionar_reporte,resumen_revision,crear_orden_subestacion,lista_ordenes_subestacion,lista_ordenes_operario,enviar_informe_final,filtrar_padres,crear_pregunta_padre,eliminar_pregunta_padre,historico_subestacion,pruebapotly,mapa_ordenes,grafico_fallas,historial_nodo,registrar_usuario,ver_ruta_nodo
urlpatterns = [
    path('', lambda request: redirect('login', permanent=False)),
    path('admin/', admin.site.urls),
    path('mantenimiento/', mantenimiento, name='mantenimiento'),
    path('login/', login_view, name='login'),
    path('inicio/', ini, name='inicio'),
    path('logout/', logout_view, name='logout'),
    path('crear-nodo/', crear_nodo, name='crear_nodo'),
    path('crear-reco/', crear_reco, name='crear_reco'),
    path('crear-comunicacion/', crear_comunicacion, name='crear_comunicacion'),
    path('crear-subestacion/', crear_subestacion, name='crear_subestacion'),
    path('crear-orden/', crear_orden, name='crear_orden'),
    path('ordenes/', lista_ordenes, name='lista_ordenes'),
    path('informe_reco/crear/<int:orden_id>/', crear_informe_reco, name='crear_informe_reco'),
    
    path('conexion-cascada/<int:nodo_id>/', conexion_cascada_view, name='detalle_nodo_reco_comunicacion'),
    path('mis-ordenes/', ordenes_creadas_ingeniero, name='ordenes_creadas_ingeniero'),
    path('ver-informe/<int:orden_id>/', ver_informe_reco, name='ver_informe_reco'),
    path('vista_general_recos/', vista_general_recos, name='vista_general_recos'),
    path('lista_recos_comunicaciones/<int:nodo_id>/', detalle_nodo_reco_comunicacion, name='lista_recos_comunicaciones'),
    path('reporte-emergencia/', reporte_emergencia, name='reporte_emergencia'),
    path('historicos-recos/<int:comunicacion_id>/', historicos_recos, name='historicos_recos'),
    path('historico-trabajos/<int:comunicacion_id>/', historico_trabajos, name='historico_trabajos'),
    path('editar-nodo-reco-comunicacion/<int:nodo_id>/', editar_nodo_reco_comunicacion,
    name='editar_nodo_reco_comunicacion' ),
    path('eliminar-comunicacion/<int:comunicacion_id>/', eliminar_comunicacion, name='eliminar_comunicacion'),
    path('historico-operario/', vista_general_recos_ope, name='vista_general_recos_ope'),
    path('dashboard-completo/', dashboard_completo, name='dashboard_completo'),
    path('elegir/', elegir_inge, name='elegir_inge'),
    path('subestaciones/', subestaciones, name='subestaciones'),
    path('subestaciones/editar/<int:id>/', editar_subestacion, name='editar_subestacion'),
    path('informe_subestacion_comu/<int:orden_id>/',crear_informe_subestacion, name='crear_informe_subestacion'),
    path('informe/subestacion/<int:orden_id>/',ver_informe_sub_comu,name='ver_informe_sub_comu'),
    path('subestaciones_comunicacion/',subestaciones_comunicacion,name='subestaciones_comunicacion'),
    path('historico_sub_comu/<int:subestacion_id>/',historico_sub_comu,name='historico_sub_comu'),
    path('mapa_cali/',mapa_nodos,name='mapa_cali'),
    path('historicos/pdf/<int:comunicacion_id>/', historicos_recos_pdf, name='historicos_recos_pdf'),
    path("subestacion/<int:orden_id>/revisar/<str:categoria>/", revisar_subestacion, name="revisar_subestacion"),
    
    path("preguntas/", lista_preguntas, name="lista_preguntas"),
    path("preguntas/crear/", crear_pregunta, name="crear_pregunta"),
    path("preguntas/eliminar/<int:id>/", eliminar_pregunta, name="eliminar_pregunta"),
    path("subestaciones-operario/", subestaciones_operario, name="subestaciones_operario"),
    path("seleccionar-reporte/<int:id>/", seleccionar_reporte, name="seleccionar_reporte"),
    path("orden/<int:orden_id>/resumen/", resumen_revision, name="resumen_revision"),
    path("orden/crear/", crear_orden_subestacion, name="crear_orden_subestacion"),
    path("ordenes_subestacion/", lista_ordenes_subestacion, name="lista_ordenes_subestacion"),
    path("ordenes_subestacion_operario/", lista_ordenes_operario, name="ordenes_subestacion_operario"),
    path("orden/<int:orden_id>/enviar-informe/", enviar_informe_final, name="enviar_informe_final"),
    path('filtrar-padres/',filtrar_padres, name='filtrar_padres'),
    path("preguntas_padre/crear/", crear_pregunta_padre, name="crear_pregunta_padre"),
    path("preguntas/eliminar/<int:id>/", eliminar_pregunta_padre, name="eliminar_pregunta_padre"),
    path("historico-subestacion/<int:subestacion_id>/", historico_subestacion, name="historico_subestacion"),
    path("pruebapilotoploty/", pruebapotly, name="pruebapotly"),
    path('registrar_usuario/',registrar_usuario, name='registrar_usuario'),
    path('mapa_ordenes/', mapa_ordenes, name='mapa_ordenes'),
    path('grafico-fallas/', grafico_fallas, name='grafico_fallas'),
    path('historial-nodo/', historial_nodo, name='historial_nodo'),
    path('ver-ruta-nodo/', ver_ruta_nodo, name='ver_ruta_nodo'),
]
