from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import LoginForm
from .forms import UsuarioRegistroForm
from .models import Trabajador,CodigoRecuperacion
from .decorators import role_required
from django.core.mail import send_mail
from django.contrib import messages
import random
def volver_loguien(request):
    return(render, login_required)

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Buscamos su rol desde el modelo Trabajador
            try:
                trabajador = Trabajador.objects.get(user=user)
                rol = trabajador.id_rol.nombre.lower()
            except Trabajador.DoesNotExist:
                rol = None

            # Redirigir según rol
            if rol == 'jefe':
                return redirect('mantenimiento')
            elif rol == 'operario':
                return redirect('lista_ordenes')
            else:
                return redirect('inicio')  # por si acaso tiene otro rol

        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def ini(request):
    return render(request, 'inicio.html')

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Max, Count, Case, When, DateTimeField, Value, CharField, F,Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.template.loader import get_template
from django.core.serializers.json import DjangoJSONEncoder
import json
import plotly.express as px
from plotly.offline import plot
from decimal import Decimal, InvalidOperation
from datetime import datetime, time, timedelta
import json
import pandas as pd
from xhtml2pdf import pisa
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    
    return redirect('login')  # Te devuelve a la página de login
# Formularios
from .forms import (
    SubestacionForm,
    SubestacionComuInformeForm,
    NodoForm,
    InformeRecoForm,
    PreguntaForm,
    OrdenSubestacionForm,
    PreguntaPadreForm,
    TresFotosForm
)

# Modelos
from .models import (
    Nodo,
    Reconectador,
    Comunicacion,
    Subestacion,
    Trabajador,
    Orden,
    InformeReco,
    ComentarioIngeniero,
    Subestacion_comu_informe,
    Historicosubcomu,
    HistoricoReco,
    ComponenteSubestacion,
    RevisionSubestacion,
    Pregunta,
    Respuesta,
    OrdenSubestacion,
    PreguntaPadre,
    HistoricoSubestacion,
    FotoInformeReco,
    Rol
)

@role_required('jefe')
def mantenimiento(request):
    # ✅ Se corrige .get8 por .get
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    orden_param = request.GET.get('orden', 'desc')  # desc = más reciente primero
    estado = request.GET.get('estado')              # filtro por estado
    tipo = request.GET.get('tipo')                  # filtro por tipo

    ordenes = Orden.objects.select_related('id_nodo', 'id_subestacion')

    # 📅 Filtro por fechas
    if fecha_inicio or fecha_fin:
        fi = parse_date(fecha_inicio) if fecha_inicio else None
        ff = parse_date(fecha_fin) if fecha_fin else None
        if fi and ff:
            ordenes = ordenes.filter(fecha__range=[fi, ff])
        elif fi:
            ordenes = ordenes.filter(fecha__gte=fi)
        elif ff:
            ordenes = ordenes.filter(fecha__lte=ff)

    # ⚙️ Filtro por estado
    if estado and estado != "todos":
        ordenes = ordenes.filter(estado_orden=estado)

    # 🧩 Filtro por tipo
    if tipo and tipo != "todos":
        ordenes = ordenes.filter(tipo=tipo)

    # 🔁 Orden ascendente o descendente
    ordenes = ordenes.order_by('fecha' if orden_param == 'asc' else '-fecha')

    # 🧾 Renderizar template
    return render(request, 'mantenimiento.html', {
        'ordenes': ordenes,
        'fecha_inicio': fecha_inicio or '',
        'fecha_fin': fecha_fin or '',
        'orden': orden_param,
        'estado': estado or 'todos',
        'tipo': tipo or 'todos',
        'estados': Orden._meta.get_field('estado_orden').choices,
        'tipos': Orden._meta.get_field('tipo').choices,
    })




# Vista para crear un nuevo nodo
@role_required('jefe')
def crear_nodo(request):
   

    # Traer todas las subestaciones desde la base de datos
    subestaciones = Subestacion.objects.all()

    if request.method == 'POST':
        # Si el método es POST, significa que el usuario envió el formulario
        form = NodoForm(request.POST)

        if form.is_valid():
            # Si el formulario es válido, guarda el nuevo nodo en la BD
            form.save()
            # Mensaje de confirmación
            messages.success(request, "Nodo registrado correctamente.")
            # Redirige nuevamente a la vista de creación de nodo
            return redirect('crear_nodo')
        else:
            # Si el formulario tiene errores, muestra mensaje de error
            messages.error(
                request,
                "Revisa los campos, puede que la Subestación no exista o falten datos."
            )
    else:
        # Si no es POST, se crea un formulario vacío para llenar
        form = NodoForm()

    # Renderizar la plantilla 'crear_nodo.html'
    # y pasar el formulario + lista de subestaciones al contexto
    return render(request, 'crear_nodo.html', {
        'form': form,
        'subestaciones': subestaciones
    })



# ----------------------------------------
# ✅ VIEW 2: Crear Reconectador
# ----------------------------------------
@role_required('jefe')
def crear_reco(request):
    if request.method == 'POST':
        sn_activo = request.POST.get('sn_activo')
        n_equipo = request.POST.get('n_equipo')
        foto = request.FILES.get('foto')  # imagen
        nodo_nombre = request.POST.get('nodo')  # nombre del nodo
        serial_reco = request.POST.get('serial')  # input: serial
        modelo = request.POST.get('modelo')
        fecha_instalacion = request.POST.get('fecha_instalacion')
        responsable = request.POST.get('responsable')
        marca = request.POST.get('marca')
        estado_reconectador = request.POST.get('estado')  # input: estado
        Icc = request.POST.get('Icc')

        # Buscar nodo
        try:
            nodo_obj = Nodo.objects.get(nodo=nodo_nombre)
        except Nodo.DoesNotExist:
            messages.error(request, "Nodo no encontrado.")
            return redirect('crear_reco')

        # Crear objeto SIN el campo "activo"
        reco = Reconectador(
            sn_activo=sn_activo,
            n_equipo=n_equipo,
            id_nodo=nodo_obj,
            serial_reco=serial_reco,
            modelo=modelo,
            fecha_instalacion=fecha_instalacion,
            responsable=responsable,
            marca=marca,
            estado_reconectador=estado_reconectador,
            Icc=Icc
        )

        # Asignar foto si la subieron
        if foto:
            reco.foto = foto

        reco.save()
        messages.success(request, "Reconectador creado exitosamente.")
        return redirect('vista_general_recos')

    # GET → mostrar formulario
    nodos = Nodo.objects.all()
    return render(request, 'crear_reco.html', {'nodos': nodos})
# ----------------------------------------
# ✅ VIEW 3: Crear Comunicación
# ----------------------------------------
@role_required('jefe')
def crear_comunicacion(request):
    if request.method == 'POST':
        modem = request.POST.get('modem')
        ip = request.POST.get('ip')
        ip_vieja = request.POST.get('ip_vieja')
        asdu = request.POST.get('asdu')
        id_reco = request.POST.get('id_reco')
        estado = request.POST.get('estado')
        tecnologia = request.POST.get('tecnologia')
        estado_actividad = request.POST.get('estado_actividad')
        serial_modem = request.POST.get('serial_modem')

        # Guardar comunicación
        Comunicacion.objects.create(
            modem=modem,
            ip=ip,
            ip_vieja=ip_vieja,
            asdu=asdu,
            id_reco_id=id_reco,
            estado=estado,
            tecnologia=tecnologia,
            estado_actividad=estado_actividad,
            serial_modem=serial_modem
        )

        messages.success(request, "Comunicación registrada exitosamente.")
        return redirect('crear_comunicacion')

    # Traemos todos los reconectadores con su nodo relacionado
    reconectadores = Reconectador.objects.select_related('id_nodo').all()

    return render(request, 'crear_comunicacion.html', {
        'reconectadores': reconectadores
    })



@role_required('jefe')
def crear_orden(request):
    if request.method == 'POST':
        n_orden = request.POST.get('n_orden')
        descripcion = request.POST.get('descripcion')
        fecha = request.POST.get('fecha')
        tipo = request.POST.get('tipo')

        # ⚡ Automático: creador = trabajador del usuario logueado
        creada_por = request.user.trabajador.id  

        asignada_a = request.POST.get('asignada_a')

        id_nodo = None
        id_subestacion = None

        if tipo == 'reco':
            nombre_nodo = request.POST.get('nombre_nodo_reco')
            try:
                nodo = Nodo.objects.get(nodo=nombre_nodo)
                id_nodo = nodo.id_nodo
            except Nodo.DoesNotExist:
                try:
                    nodo = Nodo.objects.get(nt=nombre_nodo)
                    id_nodo = nodo.id_nodo
                except Nodo.DoesNotExist:
                    messages.error(request, f"Nodo '{nombre_nodo}' no encontrado.")
                    return redirect('mantenimiento')

        elif tipo == 'subestacion':
            nombre_sub = request.POST.get('nombre_subestacion_texto')
            try:
                sub = Subestacion.objects.get(nombre=nombre_sub)
                id_subestacion = sub.id
            except Subestacion.DoesNotExist:
                messages.error(request, f"Subestación '{nombre_sub}' no encontrada.")
                return redirect('mantenimiento')

        Orden.objects.create(
            n_orden=n_orden,
            descripcion=descripcion,
            fecha=fecha,
            id_nodo_id=id_nodo,
            id_subestacion_id=id_subestacion,
            tipo=tipo,
            creada_por_id=creada_por,  # ← AUTOMÁTICO
            asignada_a_id=asignada_a,
            estado_orden='pendiente'
        )

        messages.success(request, "✅ Orden creada correctamente.")
        return redirect('mantenimiento')

    nodos = Nodo.objects.all()
    subestaciones = Subestacion.objects.all()
    operarios = Trabajador.objects.filter(id_rol__nombre='operario')

    return render(request, 'crear_orden.html', {
        'nodos': nodos,
        'subestaciones': subestaciones,
        'trabajadores_operarios': operarios,
    })




@role_required('operario')
def lista_ordenes(request):
    # --- Ordenamiento por subestación ---
    orden_param = request.GET.get('orden', 'az')

    # --- Fechas desde el GET ---
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # --- Filtro por tipo ---
    tipo_param = request.GET.get('tipo')  # 'reco' o 'subestacion'

    # Query base (excluye completadas)
    ordenes_qs = (
        Orden.objects.select_related(
            'id_nodo',
            'id_nodo__id_subestacion',
            'id_subestacion'
        )
        .exclude(estado_orden='completada')
    )

    if tipo_param in ['reco', 'subestacion']:
        ordenes_qs = ordenes_qs.filter(tipo=tipo_param)

    # --- Subestación unificada ---
    ordenes_qs = ordenes_qs.annotate(
        subestacion_nombre=Case(
            When(tipo='reco', then=F('id_nodo__id_subestacion__nombre')),
            When(tipo='subestacion', then=F('id_subestacion__nombre')),
            default=Value(''),
            output_field=CharField(),
        )
    )

    # --- Anotar última fecha de inicio ---
    ordenes_qs = ordenes_qs.annotate(
        ultimo_inicio=Case(
            When(tipo='reco', then=F('informe_reco__inicio_actividad')),
            When(tipo='subestacion', then=Max('subestacion_comu_informe__hora_inicio')),
            output_field=DateTimeField(),
        )
    )

    # --- Fecha final = último informe o fecha de la orden ---
    ordenes_qs = ordenes_qs.annotate(
        fecha_final=Coalesce('ultimo_inicio', F('fecha'))
    )

    # --- Filtros de fecha ---
    try:
        fi_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None
        ff_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None
    except ValueError:
        messages.error(request, "Formato de fecha inválido. Usa YYYY-MM-DD.")
        return render(request, 'lista_ordenes.html', {
            'ordenes': [],
            'fecha_inicio': fecha_inicio or '',
            'fecha_fin': fecha_fin or '',
            'tipo_param': tipo_param or ''
        })

    if fi_date or ff_date:
        start_dt = timezone.make_aware(datetime.combine(fi_date, time.min)) if fi_date else None
        end_dt = timezone.make_aware(datetime.combine(ff_date, time.max)) if ff_date else None

        if start_dt and end_dt:
            ordenes_qs = ordenes_qs.filter(fecha_final__range=(start_dt, end_dt))
        elif start_dt:
            ordenes_qs = ordenes_qs.filter(fecha_final__gte=start_dt)
        elif end_dt:
            ordenes_qs = ordenes_qs.filter(fecha_final__lte=end_dt)

    # --- Ordenar: primero por fecha más reciente (informe o fecha orden), luego por subestación ---
    orden_subestacion = '-subestacion_nombre' if orden_param == 'za' else 'subestacion_nombre'
    ordenes_qs = ordenes_qs.order_by('-fecha_final', orden_subestacion)

    # --- Construcción de la lista ---
    ordenes = []
    for orden in ordenes_qs:
        informe = None
        puede_editar = False

        if orden.tipo == "reco":
            informe = getattr(orden, "informe_reco", None)
        elif orden.tipo == "subestacion":
            informe = Subestacion_comu_informe.objects.filter(orden=orden).order_by('-hora_inicio').first()

        # Validar ventana de edición (2 horas)
        if informe:
            if orden.tipo == "reco" and getattr(informe, "inicio_actividad", None):
                limite = informe.inicio_actividad + timedelta(hours=2)
                puede_editar = timezone.now() <= limite
            elif orden.tipo == "subestacion" and getattr(informe, "hora_inicio", None):
                limite = informe.hora_inicio + timedelta(hours=2)
                puede_editar = timezone.now() <= limite

        ordenes.append({
            'orden': orden,
            'informe': informe,
            'puede_editar': puede_editar
        })

    return render(request, 'lista_ordenes.html', {
        'ordenes': ordenes,
        'fecha_inicio': fecha_inicio or '',
        'fecha_fin': fecha_fin or '',
        'tipo_param': tipo_param or ''
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Orden, Reconectador, InformeReco, FotoInformeReco
from .forms import InformeRecoForm, TresFotosForm

@role_required('operario')
def crear_informe_reco(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    nodo = orden.id_nodo
    reco = Reconectador.objects.filter(id_nodo=nodo).first() if nodo else None
    informe_existente = InformeReco.objects.filter(orden=orden).first()

    puede_editar = False
    if informe_existente:
        limite_tiempo = informe_existente.inicio_actividad + timedelta(hours=2)
        puede_editar = timezone.now() <= limite_tiempo

    # 🔹 POST - guardar o editar informe
    if request.method == 'POST':
        # Si existe y está dentro del tiempo permitido, se edita
        if informe_existente and puede_editar:
            mensaje = "✅ Informe editado con éxito."
        # Si no existe, se crea uno nuevo
        elif not informe_existente:
            mensaje = "✅ Informe creado con éxito."
        else:
            # 🔸 Si ya no se puede editar, solo actualiza estado y redirige
            if orden.estado_orden == 'pendiente':
                orden.estado_orden = 'pendiente_por_revisar'
                orden.save()
            return redirect('lista_ordenes')

        # Procesar los datos del formulario manualmente
        falla_identificada = request.POST.get('falla_identificada')
        causa_falla = request.POST.get('causa_falla')
        trabajo_realizado = request.POST.get('trabajo_realizado')
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')
        aviso_telco = request.POST.get('aviso_telco') == 'on'
        detalle_telco = request.POST.get('detalle_telco', '')
        aviso_mante = request.POST.get('aviso_mante') == 'on'
        detalle_mante = request.POST.get('detalle_mante', '')

        # Validar campos requeridos
        if not all([falla_identificada, causa_falla, trabajo_realizado, latitud, longitud]):
            messages.error(request, "⚠️ Todos los campos requeridos deben estar completos.")
            return render(request, 'crear_informe_reco.html', {
                'orden': orden,
                'reco': reco,
                'nodo': nodo,
                'puede_editar': puede_editar,
                'informe_existente': informe_existente,
            })

        # Crear o actualizar el informe
        if informe_existente and puede_editar:
            informe = informe_existente
        else:
            informe = InformeReco(orden=orden)
            # Guardar fecha de inicio si es nuevo
            inicio = request.session.get('inicio_actividad')
            if inicio:
                try:
                    inicio = timezone.datetime.fromisoformat(inicio)
                except ValueError:
                    inicio = timezone.now()
            else:
                inicio = timezone.now()
            informe.inicio_actividad = inicio

        # Asignar campos
        informe.falla_identificada = falla_identificada
        informe.causa_falla = causa_falla
        informe.trabajo_realizado = trabajo_realizado
        informe.latitud = latitud
        informe.longitud = longitud
        informe.aviso_telco = aviso_telco
        informe.detalle_telco = detalle_telco
        informe.aviso_mante = aviso_mante
        informe.detalle_mante = detalle_mante
        informe.hora_cierre = timezone.now()
        
        informe.save()

        # 🔹 Guardar fotos
        for campo in ['foto1', 'foto2', 'foto3']:
            archivo = request.FILES.get(campo)
            if archivo and informe.fotos.count() < 3:
                FotoInformeReco.objects.create(informe=informe, imagen=archivo)

        # 🔹 Actualizar orden
        orden.estado_orden = 'pendiente_por_revisar'
        orden.save()

        # 🔹 Limpiar sesión
        request.session.pop('inicio_actividad', None)

        messages.success(request, mensaje)
        return redirect('lista_ordenes')

    # 🔹 GET - mostrar formulario
    else:
        if not informe_existente:
            request.session['inicio_actividad'] = timezone.now().isoformat()

    # 🔹 Contexto
    contexto = {
        'orden': orden,
        'reco': reco,
        'nodo': nodo,
        'puede_editar': puede_editar,
        'informe_existente': informe_existente,
    }

    return render(request, 'crear_informe_reco.html', contexto)


def conexion_cascada_view(request, nodo_id=None):
    if nodo_id:
        nodos = [get_object_or_404(Nodo, id_nodo=nodo_id)]
    else:
        nodos = Nodo.objects.all()
    
    return render(request, 'conexion_cascada.html', {'nodos': nodos})


def ordenes_creadas_ingeniero(request):
    usuario = request.user.trabajador  # suponiendo que usas auth
    ordenes = Orden.objects.filter(creada_por=usuario)
    return render(request, 'ordenes_creadas_ingeniero.html', {'ordenes': ordenes})

# Ver el informe completado por el trabajador
def ver_informe_reco(request, orden_id):
    informe = get_object_or_404(InformeReco, orden__id=orden_id)
    orden = informe.orden

    if request.method == 'POST' and 'completada' in request.POST:
        orden.estado_orden = 'completada'
        orden.save()
        return redirect('ver_informe_reco', orden_id=orden_id)

    comunicacion_id = None
    if orden.id_nodo:
        reco = Reconectador.objects.filter(id_nodo=orden.id_nodo).first()
        if reco:
            comunicacion = Comunicacion.objects.filter(id_reco=reco).first()
            if comunicacion:
                comunicacion_id = comunicacion.id_comunicacion

    return render(
        request,
        'ver_informe_reco.html',
        {
            'informe': informe,
            'comunicacion_id': comunicacion_id
        }
    )

def vista_general_recos(request):
    """
    Vista que muestra un resumen general de los nodos, 
    sus reconectadores y las comunicaciones asociadas.

    Esta vista:
        - Obtiene todos los nodos de la base de datos.
        - Usa ``prefetch_related`` para optimizar la carga de:
            * los reconectadores asociados a cada nodo.
            * las comunicaciones asociadas a cada reconectador.
        - Renderiza la plantilla ``vista_general_recos.html``.

    Contexto enviado al template:
        nodos (QuerySet): Lista de objetos `Nodo` con sus
        reconectadores y comunicaciones precargados.
    """
    nodos = Nodo.objects.prefetch_related('reconectador_set__comunicacion_set').all()
    return render(request, 'vista_general_recos.html', {'nodos': nodos})



# Vista para mostrar el detalle de un nodo con su reco y comunicación asociada
def detalle_nodo_reco_comunicacion(request, nodo_id):
    # Buscar el nodo en la base de datos o devolver un 404 si no existe
    nodo = get_object_or_404(Nodo, id_nodo=nodo_id)

    # Traer el primer reconectador asociado al nodo (si existe)
    reco = Reconectador.objects.filter(id_nodo=nodo).first()

    # Si el reco existe, traer la primera comunicación asociada
    comunicacion = Comunicacion.objects.filter(id_reco=reco).first() if reco else None

    # Capturar el parámetro 'from' de la URL para saber de dónde viene la navegación
    # Si no existe, usar "mantenimiento" como valor por defecto
    origen_param = request.GET.get("from", "mantenimiento")

    try:
        # Intentar construir la URL de origen dinámicamente
        url_origen = reverse(origen_param)
    except:
        # Si falla (p. ej. no existe la ruta), redirigir a "mantenimiento"
        url_origen = reverse("mantenimiento")

    # Renderizar la plantilla 'lista_recos_comunicaciones.html'
    # pasando el nodo, su reco, la comunicación y la URL de origen
    return render(request, 'lista_recos_comunicaciones.html', {
        'nodo': nodo,
        'reco': reco,
        'comunicacion': comunicacion,
        'url_origen': url_origen  # <-- se pasa al template para el botón "Volver"
    })

@role_required('operario')
def reporte_emergencia(request):
    nodos = Nodo.objects.all()
    subestaciones = Subestacion.objects.all()

    if request.method == 'POST':
        try:
            nodo_input = request.POST.get('nodo_nombre')
            tipo = request.POST.get('tipo')

            # -----------------------------
            # VALIDACIONES BÁSICAS
            # -----------------------------
            if not nodo_input:
                messages.error(request, "Debe seleccionar un nodo o subestación.")
                return render(request, 'reporte_emergencia_completo.html', {
                    'nodos': nodos,
                    'subestaciones': subestaciones,
                    'tipos': Orden.TIPO_CHOICES
                })

            if tipo not in ['reco', 'subestacion']:
                messages.error(request, "Debe seleccionar un tipo válido.")
                return render(request, 'reporte_emergencia_completo.html', {
                    'nodos': nodos,
                    'subestaciones': subestaciones,
                    'tipos': Orden.TIPO_CHOICES
                })

            # -----------------------------
            # OBTENER OBJETO NODO/SUBESTACIÓN
            # -----------------------------
            nodo_obj, sub_obj = None, None

            if tipo == 'reco':
                nodo_obj = Nodo.objects.get(nodo=int(nodo_input))
            else:
                sub_obj = Subestacion.objects.get(nombre=nodo_input)

            # -----------------------------
            # COORDENADAS
            # -----------------------------
            def parse_decimal(value):
                try:
                    return Decimal(value) if value else None
                except InvalidOperation:
                    return None

            latitud = parse_decimal(request.POST.get('latitud'))
            longitud = parse_decimal(request.POST.get('longitud'))

            # -----------------------------
            # FECHAS
            # -----------------------------
            inicio_dt = timezone.now()

            # -----------------------------
            # TRABAJADOR
            # -----------------------------
            try:
                trabajador = Trabajador.objects.get(user=request.user)
            except Trabajador.DoesNotExist:
                messages.error(request, "No existe un trabajador asociado a este usuario.")
                return redirect('reporte_emergencia')

            # -----------------------------
            # CREAR ORDEN
            # -----------------------------
            orden = Orden.objects.create(
                tipo=tipo,
                descripcion='Reporte de emergencia',
                id_nodo=nodo_obj if tipo == 'reco' else None,
                id_subestacion=sub_obj if tipo == 'subestacion' else None,
                estado_orden='pendiente_por_revisar',
                fecha=timezone.now().date(),
                n_orden='EMERG-' + timezone.now().strftime('%Y%m%d%H%M%S'),
                creada_por=trabajador,
                asignada_a=None
            )

            # -----------------------------
            # CREAR INFORME RECO — COMPLETO
            # -----------------------------
            if tipo == 'reco':
                informe = InformeReco.objects.create(
                    orden=orden,
                    inicio_actividad=inicio_dt,
                    falla_identificada=request.POST.get('falla_identificada'),
                    causa_falla=request.POST.get('causa_falla'),
                    trabajo_realizado=request.POST.get('trabajo_realizado'),
                    hora_cierre=timezone.now(),
                    longitud=longitud,
                    latitud=latitud,

                    # ✔ NUEVO → Telco / Mantenimiento
                    aviso_telco=request.POST.get('aviso_telco') == 'on',
                    detalle_telco=request.POST.get('detalle_telco'),
                    aviso_mante=request.POST.get('aviso_mante') == 'on',
                    detalle_mante=request.POST.get('detalle_mante'),
                )

                # -----------------------------
                # FOTOS (máximo 3)
                # -----------------------------
                for campo in ['foto1', 'foto2', 'foto3']:
                    archivo = request.FILES.get(campo)
                    if archivo:
                        FotoInformeReco.objects.create(informe=informe, imagen=archivo)

            # -----------------------------
            # INFORME SUBESTACIÓN
            # -----------------------------
            else:
                Subestacion_comu_informe.objects.create(
                    orden=orden,
                    hora_inicio=inicio_dt,
                    trabajo_realizado_sub_comu=request.POST.get('trabajo_realizado_sub_comu'),
                    otras_observaciones=request.POST.get('otras_observaciones'),
                    hora_cierre=timezone.now(),
                    longitud_sub=longitud,
                    latitud_sub=latitud,
                )

            messages.success(request, "✅ Reporte de emergencia creado exitosamente.")
            return redirect('lista_ordenes')

        except Exception as e:
            print("ERROR:", e)
            messages.error(request, "Error creando el reporte. Verifique los datos.")

    # -----------------------------
    # GET
    # -----------------------------
    return render(request, 'reporte_emergencia_completo.html', {
        'nodos': nodos,
        'subestaciones': subestaciones,
        'tipos': Orden.TIPO_CHOICES
    })

def historicos_recos(request, comunicacion_id):
    # Intentar obtener la comunicación
    comunicacion = Comunicacion.objects.filter(id_comunicacion=comunicacion_id).first()

    # Obtener reco y nodo (si la comunicación existía)
    reco = comunicacion.id_reco if comunicacion else None
    nodo = reco.id_nodo if reco else None

    # 1️⃣ Informes del nodo (solo si hay nodo)
    informes = InformeReco.objects.filter(
        orden__id_nodo=nodo,
        orden__tipo='reco'
    ).order_by('-hora_cierre') if nodo else []

    # 2️⃣ Comentarios del histórico:
    #    Si la comunicación existe → filtramos normalmente
    #    Si fue eliminada → buscamos comentarios que quedaron con id_comunicacion=None
    comentarios = ComentarioIngeniero.objects.filter(
        Q(id_comunicacion_id=comunicacion_id) | Q(id_comunicacion__isnull=True)
    ).order_by('-creado')

    # 3️⃣ Manejo de formularios
    if request.method == 'POST':
        # Cambio de estado del reco
        if 'estado_reco' in request.POST and reco:
            nuevo_estado = request.POST.get('estado_reco')
            if nuevo_estado:
                reco.estado_reconectador = nuevo_estado
                reco.save()
                messages.success(request, f"Has cambiado el estado del reconectador a: {nuevo_estado}")

        # Nuevo comentario
        if 'comentario_ingeniero' in request.POST:
            texto = request.POST.get('comentario_ingeniero')
            if texto:
                ComentarioIngeniero.objects.create(
                    id_comunicacion=comunicacion,  # puede ser None si ya fue eliminada
                    texto=texto
                )
                messages.success(request, "Comentario guardado correctamente.")

        return redirect('historicos_recos', comunicacion_id=comunicacion_id)

    # 4️⃣ Renderizar con contexto (aunque la comunicación no exista)
    return render(request, 'historicos_recos.html', {
        'comunicacion': comunicacion,  # puede ser None
        'reco': reco,
        'nodo': nodo,
        'informes': informes,
        'comentarios': comentarios,
    })

def historico_trabajos(request, comunicacion_id):
    comunicacion = get_object_or_404(Comunicacion, id_comunicacion=comunicacion_id)
    reco = comunicacion.id_reco
    nodo = reco.id_nodo

    # Solo obtener informes relacionados a esa comunicación
    informes = InformeReco.objects.filter(
        orden__id_nodo=nodo,
        orden__tipo='reco'
    ).order_by('-hora_cierre')

    return render(request, 'historico_solo_lectura.html', {
        'comunicacion': comunicacion,
        'reco': reco,
        'nodo': nodo,
        'informes': informes,
    })    

def editar_nodo_reco_comunicacion(request, nodo_id):
    nodo = get_object_or_404(Nodo, id_nodo=nodo_id)
    reco = Reconectador.objects.filter(id_nodo=nodo).first()
    comunicacion = Comunicacion.objects.filter(id_reco=reco).first() if reco else None

    if request.method == 'POST':
        if reco:
            reco.sn_activo = request.POST.get('sn_activo')
            reco.activo_reco = request.POST.get('activo_reco')
            reco.n_equipo = request.POST.get('n_equipo')
            reco.serial_reco = request.POST.get('serial_reco')
            reco.modelo = request.POST.get('modelo')
            reco.marca = request.POST.get('marca')

            # 🔧 Manejo correcto de la fecha
            fecha_instalacion = request.POST.get('fecha_instalacion')
            if fecha_instalacion:
                reco.fecha_instalacion = fecha_instalacion
            else:
                reco.fecha_instalacion = None

            reco.responsable = request.POST.get('responsable')
            reco.estado_bateria = request.POST.get('estado_bateria')
            reco.serial_bateria = request.POST.get('serial_bateria')
            reco.estado_reconectador = request.POST.get('estado_reconectador')
            reco.Icc = request.POST.get('Icc')

            # 📸 Manejo de la foto
            if 'foto' in request.FILES:
                reco.foto = request.FILES['foto']

            reco.save()

        if comunicacion:
            comunicacion.modem = request.POST.get('modem')
            comunicacion.activo_modem = request.POST.get('activo_modem')
            comunicacion.ip = request.POST.get('ip')
            comunicacion.ip_vieja = request.POST.get('ip_vieja')
            comunicacion.asdu = request.POST.get('asdu')
            comunicacion.estado = request.POST.get('estado')
            comunicacion.tecnologia = request.POST.get('tecnologia')
            comunicacion.estado_actividad = request.POST.get('estado_actividad')
            comunicacion.serial_modem = request.POST.get('serial_modem')
            comunicacion.save()

        messages.success(request, "Datos actualizados correctamente.")
        return redirect('vista_general_recos')

    return render(request, 'editar_nodo_reco_comunicacion.html', {
        'nodo': nodo,
        'reco': reco,
        'comunicacion': comunicacion
    })


# Vista para eliminar una comunicación específica
def eliminar_comunicacion(request, comunicacion_id):
    # Buscamos la comunicación con el ID proporcionado.
    # Si no existe, devuelve un error 404.
    comunicacion = get_object_or_404(Comunicacion, id_comunicacion=comunicacion_id)

    # Eliminamos la comunicación de la base de datos.
    comunicacion.delete()

    # Mostramos un mensaje de confirmación al usuario.
    messages.success(request, "Comunicación eliminada correctamente.")

    # Redirigimos a la vista general de recos después de eliminar.
    return redirect('vista_general_recos')



# Vista para mostrar una vista general de los nodos, sus recos y comunicaciones (versión operador)
def vista_general_recos_ope(request):
    # Consultamos todos los nodos y, con prefetch_related,
    # traemos de forma optimizada los recos y las comunicaciones asociadas
    # Esto evita múltiples consultas a la base de datos (mejora el rendimiento).
    nodos = Nodo.objects.prefetch_related('reconectador_set__comunicacion_set').all()

    # Renderizamos la plantilla 'vista_general_recos_ope.html',
    # enviando la lista de nodos (con sus recos y comunicaciones)
    return render(request, 'vista_general_recos_ope.html', {'nodos': nodos})




def dashboard_completo(request):
    # ==========================
    # 1. Totales generales
    # ==========================
    total_nodos = Reconectador.objects.values('id_nodo').distinct().count()
    total_subestaciones = Reconectador.objects.values('id_nodo__id_subestacion').distinct().count()
    total_recos = Reconectador.objects.count()
    total_comunicaciones = Comunicacion.objects.count()

    # ==========================
    # 2. Recos por subestación
    # ==========================
    recos_por_subestacion = (
        Reconectador.objects
        .values('id_nodo__id_subestacion__nombre')
        .annotate(total=Count('id_reco'))
        .order_by('id_nodo__id_subestacion__nombre')
    )
    subestaciones = [r['id_nodo__id_subestacion__nombre'] for r in recos_por_subestacion]
    recos_subestacion = [r['total'] for r in recos_por_subestacion]

    # ==========================
    # 3. Comunicaciones por estado
    # ==========================
    comunicaciones_por_estado = (
        Comunicacion.objects
        .values('estado')
        .annotate(total=Count('id_comunicacion'))
        .order_by('estado')
    )
    estados = [r['estado'] if r['estado'] else 'Sin estado' for r in comunicaciones_por_estado]
    total_por_estado = [r['total'] for r in comunicaciones_por_estado]

    # ==========================
    # 4. Actividad comunicaciones (todas)
    # ==========================
    actividad_comunicaciones = (
        Comunicacion.objects
        .values('estado_actividad')
        .annotate(total=Count('id_comunicacion'))
        .order_by('estado_actividad')
    )
    actividad_labels = [
        r['estado_actividad'] if r['estado_actividad'] not in [None, '', 'nan'] else 'Sin dato'
        for r in actividad_comunicaciones
    ]
    actividad_totales = [r['total'] for r in actividad_comunicaciones]

    # ==========================
    # 5. Módems por tecnología
    # ==========================
    modems_por_tecnologia = (
        Comunicacion.objects
        .values('tecnologia')
        .annotate(total=Count('id_comunicacion'))
        .order_by('tecnologia')
    )
    tecnologias = [m['tecnologia'] if m['tecnologia'] else 'Sin dato' for m in modems_por_tecnologia]
    total_tecnologias = [m['total'] for m in modems_por_tecnologia]

    # ==========================
    # 6. Desglose "pendiente operacion" por actividad
    # ==========================
    pendiente_operacion = (
        Comunicacion.objects
        .filter(estado__iexact="pendiente operacion")
        .values('estado_actividad')
        .annotate(total=Count('id_comunicacion'))
        .order_by('estado_actividad')
    )
    pendiente_labels = [
        p['estado_actividad'] if p['estado_actividad'] not in [None, '', 'nan'] else 'Sin dato'
        for p in pendiente_operacion
    ]
    pendiente_totales = [p['total'] for p in pendiente_operacion]

    # ==========================
    # 7. Desglose "RI OBSOLETO" por actividad
    # ==========================
    ri_obsoleto = (
        Comunicacion.objects
        .filter(estado__iexact="RI OBSOLETO")
        .values('estado_actividad')
        .annotate(total=Count('id_comunicacion'))
        .order_by('estado_actividad')
    )
    ri_obsoleto_labels = [
        r['estado_actividad'] if r['estado_actividad'] not in [None, '', 'nan'] else 'Sin dato'
        for r in ri_obsoleto
    ]
    ri_obsoleto_totales = [r['total'] for r in ri_obsoleto]

    # ==========================
    # 8. Capturar vista de origen y resolver URL
    # ==========================
    origen_param = request.GET.get("from", "mantenimiento")
    try:
        url_origen = reverse(origen_param)
    except:
        url_origen = reverse("mantenimiento")

    # ==========================
    # Render
    # ==========================
    context = {
        'total_nodos': total_nodos,
        'total_subestaciones': total_subestaciones,
        'total_recos': total_recos,
        'total_comunicaciones': total_comunicaciones,
        'subestaciones': subestaciones,
        'recos_subestacion': recos_subestacion,
        'estados': estados,
        'total_por_estado': total_por_estado,
        'actividad_labels': actividad_labels,
        'actividad_totales': actividad_totales,
        'tecnologias': tecnologias,
        'total_tecnologias': total_tecnologias,
        'comunicaciones_estados_labels': estados,
        'comunicaciones_estados_totales': total_por_estado,
        'pendiente_labels': pendiente_labels,
        'pendiente_totales': pendiente_totales,
        'ri_obsoleto_labels': ri_obsoleto_labels,
        'ri_obsoleto_totales': ri_obsoleto_totales,
        'url_origen': url_origen,   # 👈 pasamos la URL lista al template
    }
    return render(request, 'dashboard_completo.html', context)



def elegir_inge(request):
    # aquí puedes pasar contexto si quieres
     
    return render(request, 'elegir_inge.html')

# Vista para mostrar todas las subestaciones
def subestaciones(request):
    # Trae todas las subestaciones desde la base de datos
    subestaciones = Subestacion.objects.all()
    
    # Renderiza la plantilla 'vista_subestaciones.html'
    # y le pasa el listado de subestaciones en el contexto
    return render(request, 'vista_subestaciones.html', {"subestaciones": subestaciones})

# Editar una subestación existente
def editar_subestacion(request, id):
    subestacion = get_object_or_404(Subestacion, pk=id)

    if request.method == 'POST':
        form = SubestacionForm(request.POST, instance=subestacion)

        if form.is_valid():
            form.save()

            # 🔹 Actualizar componentes existentes
            componentes_existentes = request.POST.getlist("componentes_existentes[]")
            tipos_existentes = request.POST.getlist("tipos_existentes[]")
            ids_existentes = request.POST.getlist("ids_existentes[]")

            for idx, comp_id in enumerate(ids_existentes):
                try:
                    componente = ComponenteSubestacion.objects.get(
                        id_componente_sube=comp_id,
                        subestacion=subestacion
                    )
                    componente.nombre_componente = componentes_existentes[idx]
                    componente.tipo = tipos_existentes[idx]
                    componente.save()
                except:
                    pass

            # 🔹 Crear nuevos componentes
            nuevos_componentes = request.POST.getlist("componentes[]")
            nuevos_tipos = request.POST.getlist("tipos[]")
            for idx, nombre in enumerate(nuevos_componentes):
                if nombre.strip():
                    ComponenteSubestacion.objects.create(
                        nombre_componente=nombre,
                        tipo=nuevos_tipos[idx],
                        subestacion=subestacion
                    )

            # 🔹 Eliminar componentes seleccionados
            ids_a_eliminar = request.POST.getlist("eliminar_componentes")
            if ids_a_eliminar:
                ComponenteSubestacion.objects.filter(
                    id_componente_sube__in=ids_a_eliminar,
                    subestacion=subestacion
                ).delete()

            return redirect('subestaciones')

    else:
        form = SubestacionForm(instance=subestacion)

    componentes_existentes = ComponenteSubestacion.objects.filter(subestacion=subestacion)

    return render(request, 'form.html', {
        'form': form,
        'componentes_existentes': componentes_existentes,
    })
# Crear una nueva subestación
def crear_subestacion(request):
    if request.method == 'POST':
        # Cargar datos enviados desde el formulario
        form = SubestacionForm(request.POST)
        
        # Validar los datos del formulario
        if form.is_valid():
            form.save()  # Guarda la subestación en la base de datos
            return redirect('mantenimiento')  # Redirige a la vista de mantenimiento después de guardar
    else:
        # Si la petición no es POST, mostrar un formulario vacío
        form = SubestacionForm()

    # Renderizar el formulario en la plantilla
    return render(request, 'crear_subestacion.html', {'form': form})


def crear_informe_subestacion(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    informe_existente = Subestacion_comu_informe.objects.filter(orden=orden).first()

    # 🔒 Control de edición (2 horas desde hora_inicio)
    puede_editar = False
    if informe_existente and informe_existente.hora_inicio:
        limite_tiempo = informe_existente.hora_inicio + timedelta(hours=2)
        puede_editar = timezone.now() <= limite_tiempo

    if request.method == "POST":
        # 👉 Si existe y no puede editar, solo cambia estado
        if informe_existente and not puede_editar:
            if orden.estado_orden == "pendiente":
                orden.estado_orden = "pendiente_por_revisar"
                orden.save(update_fields=["estado_orden"])
            messages.warning(request, "⏳ El tiempo de edición expiró. Solo se actualizó el estado de la orden.")
            return redirect("lista_ordenes")

        form = SubestacionComuInformeForm(request.POST, instance=informe_existente)
        if form.is_valid():
            informe = form.save(commit=False)
            informe.orden = orden

            # ⏱️ hora_inicio: solo si aún no tiene
            if not informe.hora_inicio:
                inicio_actividad = request.session.get('inicio_actividad_sub')
                if inicio_actividad:
                    try:
                        informe.hora_inicio = timezone.datetime.fromisoformat(inicio_actividad)
                    except Exception:
                        informe.hora_inicio = timezone.now()
                    request.session.pop('inicio_actividad_sub', None)
                else:
                    informe.hora_inicio = timezone.now()

            # ⏱️ hora_cierre siempre al enviar
            informe.hora_cierre = timezone.now()
            informe.save()

            # ✅ Actualizar estado de la orden
            if orden.estado_orden == "pendiente":
                orden.estado_orden = "pendiente_por_revisar"
                orden.save(update_fields=["estado_orden"])

            # 🔔 Mensaje de éxito según si se creó o editó
            if informe_existente:
                messages.success(request, "✅ Informe editado con éxito.")
            else:
                messages.success(request, "✅ Informe creado con éxito.")

            return redirect("lista_ordenes")
        else:
            # 👀 DEBUG: imprime errores en consola
            print("❌ Errores de validación:", form.errors)

    else:
        # GET: prellenar si existe
        if informe_existente:
            form = SubestacionComuInformeForm(instance=informe_existente)
        else:
            form = SubestacionComuInformeForm()
            if 'inicio_actividad_sub' not in request.session:
                request.session['inicio_actividad_sub'] = timezone.now().isoformat()

    return render(
        request,
        "crear_informe_subestacion.html",
        {
            "form": form,
            "orden": orden,
            "informe": informe_existente,
            "puede_editar": puede_editar,
        },
    )

def ver_informe_sub_comu(request, orden_id):
    # Obtener el informe de la subestación
    informe = get_object_or_404(Subestacion_comu_informe, orden__id=orden_id)
    orden = informe.orden

    if request.method == 'POST':
        form = SubestacionComuInformeForm(request.POST, instance=informe)
        if 'completada' in request.POST:
            orden.estado_orden = 'completada'
            orden.save()
            return redirect('ver_informe_sub_comu', orden_id=orden_id)
        elif form.is_valid():
            form.save()
            messages.success(request, "Informe actualizado correctamente")
            return redirect('ver_informe_sub_comu', orden_id=orden_id)
    else:
        form = SubestacionComuInformeForm(instance=informe)  # Cargar los datos existentes

    return render(
        request,
        'ver_informe_sub_comu.html',
        {
            'informe': informe,
            'form': form
        }
    )

# Vista para consultar y guardar en el histórico los informes asociados a una subestación
def historico_sub_comu(request, subestacion_id):
    # 1. Filtrar informes que pertenecen a la subestación indicada
    informes = Subestacion_comu_informe.objects.filter(
        orden__id_subestacion__id=subestacion_id
    )

    # 2. Registrar en el histórico los informes obtenidos
    #    Si un informe ya existe en el histórico, no se duplica gracias a get_or_create
    for informe in informes:
        Historicosubcomu.objects.get_or_create(informe_sub_comu=informe)

    # ==========================
    # 3. Capturar el parámetro 'from' de la URL para saber desde qué vista se llamó
    #    Si no existe, por defecto se usa 'mantenimiento'
    # ==========================
    origen_param = request.GET.get("from", "mantenimiento")
    try:
        # Intentamos generar la URL de retorno según el parámetro recibido
        url_origen = reverse(origen_param)
    except:
        # Si falla (ejemplo: parámetro no corresponde a una ruta válida), volvemos a mantenimiento
        url_origen = reverse("mantenimiento")

    # 4. Renderizar la plantilla con los informes, la subestación y la URL de retorno
    return render(request, 'historico_sub_comu.html', {
        'informes': informes,                          # Informes de la subestación
        'subestacion': Subestacion.objects.get(id=subestacion_id),  # Datos de la subestación
        'url_origen': url_origen,                      # URL de retorno para navegación
    })


def subestaciones_comunicacion(request):
    subestaciones=Subestacion.objects.all()
    return render(request,'sub_comunicaciones.html', {
        'subestaciones': subestaciones
    })

# Vista para mostrar en un mapa los nodos existentes
def mapa_nodos(request):
    # Obtenemos todos los nodos de la base de datos y los convertimos en un diccionario
    # con los campos que interesan para el mapa (id, nombre, dirección, latitud y longitud).
    nodos = list(Nodo.objects.all().values(
        'id_nodo',       # ID del nodo
        'nodo',          # Numero del nodo
        'direccion',     # Dirección del nodo
        'latitud',       # Latitud geográfica
        'longitud'       # Longitud geográfica
    ))

    # Renderizamos la plantilla 'mapa_sube.html' enviando los nodos como JSON
    # para que el frontend (JavaScript) pueda dibujarlos en el mapa.
    return render(request, "mapa_sube.html", {
        "nodos": json.dumps(nodos, cls=DjangoJSONEncoder)
    })


# Vista para generar un PDF con el histórico de informes y comentarios de un reconectador
def historicos_recos_pdf(request, comunicacion_id):
    # 1. Obtener comunicación, reconectador y nodo asociado
    comunicacion = get_object_or_404(Comunicacion, id_comunicacion=comunicacion_id)
    reco = comunicacion.id_reco    # Reconectador relacionado con la comunicación
    nodo = reco.id_nodo            # Nodo al que pertenece el reconectador

    # 2. Consultar los informes relacionados con el nodo (columna izquierda del PDF)
    informes = InformeReco.objects.filter(
        orden__id_nodo=nodo,       # Solo informes del nodo actual
        orden__tipo='reco'         # Solo los de tipo 'reco'
    ).order_by('-hora_cierre')     # Ordenados por fecha de cierre más reciente primero

    # 3. Consultar los comentarios asociados directamente a la comunicación (columna derecha del PDF)
    comentarios = ComentarioIngeniero.objects.filter(
        id_comunicacion=comunicacion
    ).order_by('-creado')          # Ordenados por fecha de creación más reciente primero

    # 4. Renderizar la plantilla HTML con la información obtenida
    template = get_template('historicos_recos_pdf.html')
    html = template.render({
        'comunicacion': comunicacion,
        'reco': reco,
        'nodo': nodo,
        'informes': informes,
        'comentarios': comentarios,
    })

    # 5. Preparar respuesta HTTP para descargar el archivo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="historicos_{reco.n_equipo}.pdf"'

    # 6. Generar el PDF a partir del HTML con xhtml2pdf (pisa)
    pisa_status = pisa.CreatePDF(html, dest=response)

    # 7. Validar si hubo errores durante la creación del PDF
    if pisa_status.err:
        return HttpResponse('Error al generar PDF <pre>' + html + '</pre>')

    # 8. Retornar el PDF generado como respuesta al navegador
    return response




def revisar_subestacion(request, orden_id, categoria):
    orden = get_object_or_404(OrdenSubestacion, pk=orden_id)
    subestacion = orden.id_subestacion

    # Mapeo para categorías que requieren componentes específicos
    tipo_map = {
        "bahia": "circuito",
        "transformador": "transformador", 
        "servicios": "servicios",
        # "observaciones" no necesita mapeo porque no usa componentes
    }
    
    tipo = tipo_map.get(categoria)
    
    # Obtener componentes SOLO para categorías que los necesitan
    if categoria in ["bahia", "transformador", "servicios"]:
        componentes = subestacion.componentes.filter(tipo=tipo)
    else:
        # Para "observaciones", no filtramos por componentes
        componentes = [None]  # Lista con un elemento None para iterar

    # Obtener preguntas de la categoría
    preguntas = Pregunta.objects.filter(categoria=categoria).select_related("padre")

    preguntas_por_padre, preguntas_sin_padre = {}, []
    for preg in preguntas:
        if preg.padre:
            preguntas_por_padre.setdefault(preg.padre.id, []).append(preg)
        else:
            preguntas_sin_padre.append(preg)

    # ================================
    # Guardar POST - SOLO LO QUE SE LLENÓ
    # ================================
    if request.method == "POST":
        respuestas_temporales = request.session.get("respuestas_temporales", {})
        orden_key = str(orden.id_orden)
        
        # Inicializar estructura si no existe
        if orden_key not in respuestas_temporales:
            respuestas_temporales[orden_key] = {}
        if categoria not in respuestas_temporales[orden_key]:
            respuestas_temporales[orden_key][categoria] = {}

        # Guardar SOLO los campos que tienen valor (no vacíos)
        for componente in componentes:
            # Para "observaciones", usamos un componente virtual
            comp_id = componente.id_componente_sube if componente else "obs_general"
            
            # Preguntas sin padre
            for preg in preguntas_sin_padre:
                key = f"comp_{comp_id}_preg_{preg.id}"
                valor = request.POST.get(key, "").strip()
                
                # Solo guardar si tiene valor
                if valor:
                    respuestas_temporales[orden_key][categoria][key] = valor
                # Si existe pero ahora está vacío, eliminarlo
                elif key in respuestas_temporales[orden_key][categoria]:
                    del respuestas_temporales[orden_key][categoria][key]

            # Preguntas con padre
            for padre_id, lista_preg in preguntas_por_padre.items():
                for preg in lista_preg:
                    key = f"comp_{comp_id}_padre_{padre_id}_preg_{preg.id}"
                    valor = request.POST.get(key, "").strip()
                    
                    # Solo guardar si tiene valor
                    if valor:
                        respuestas_temporales[orden_key][categoria][key] = valor
                    # Si existe pero ahora está vacío, eliminarlo
                    elif key in respuestas_temporales[orden_key][categoria]:
                        del respuestas_temporales[orden_key][categoria][key]

        # Observaciones generales (campo adicional)
        obs = request.POST.get("observaciones_generales", "").strip()
        if obs:
            respuestas_temporales[orden_key]["observaciones_generales"] = obs
        elif "observaciones_generales" in respuestas_temporales[orden_key]:
            del respuestas_temporales[orden_key]["observaciones_generales"]

        # Eliminar categoría vacía
        if not respuestas_temporales[orden_key][categoria]:
            del respuestas_temporales[orden_key][categoria]

        request.session["respuestas_temporales"] = respuestas_temporales
        request.session.modified = True
        messages.success(request, f"Respuestas de {categoria} guardadas en memoria.")
        return redirect("seleccionar_reporte", id=orden.id_orden)

    # ================================
    # Preparar valores para el template
    # ================================
    valores_campos = {}

    # Obtener respuestas guardadas en BD
    try:
        revision = RevisionSubestacion.objects.get(orden=orden)
        respuestas_guardadas = Respuesta.objects.filter(
            revision=revision,
            pregunta__categoria=categoria
        ).select_related("pregunta", "componente")

        for resp in respuestas_guardadas:
            if resp.componente:
                comp_id = resp.componente.id_componente_sube
            else:
                comp_id = "obs_general"
                
            if resp.pregunta.padre:
                key = f"comp_{comp_id}_padre_{resp.pregunta.padre.id}_preg_{resp.pregunta.id}"
            else:
                key = f"comp_{comp_id}_preg_{resp.pregunta.id}"
            valores_campos[key] = resp.respuesta
    except RevisionSubestacion.DoesNotExist:
        pass  # No hay revisión aún, continuar

    # Obtener respuestas de sesión
    respuestas_sesion = (
        request.session.get("respuestas_temporales", {})
        .get(str(orden.id_orden), {})
        .get(categoria, {})
    )
    valores_campos.update(respuestas_sesion)

    obs_sesion = request.session.get("respuestas_temporales", {}).get(str(orden.id_orden), {}).get("observaciones_generales", "")
    if obs_sesion:
        valores_campos["observaciones_generales"] = obs_sesion

    # ================================
    # Generar estructuras para el template
    # ================================
    
    componentes_con_preguntas = []
    
    for componente in componentes:
        # Para "observaciones", creamos un objeto componente virtual
        if componente is None:
            componente_virtual = type('Obj', (), {
                'id_componente_sube': 'obs_general',
                'nombre_componente': 'Observaciones Generales',
                'get_tipo_display': lambda: 'Observaciones'
            })()
            comp_data = {
                'componente': componente_virtual,
                'preguntas_sin_padre': [],
                'preguntas_con_padre': {}
            }
        else:
            comp_data = {
                'componente': componente,
                'preguntas_sin_padre': [],
                'preguntas_con_padre': {}
            }
        
        comp_id = componente.id_componente_sube if componente else "obs_general"
        
        # Preguntas sin padre para este componente
        for preg in preguntas_sin_padre:
            key = f"comp_{comp_id}_preg_{preg.id}"
            comp_data['preguntas_sin_padre'].append({
                "pregunta": preg,
                "key": key,
                "valor": valores_campos.get(key, ""),
            })
        
        # Preguntas con padre para este componente, agrupadas por padre
        for padre_id, lista_preg in preguntas_por_padre.items():
            padre_key = f"padre_{padre_id}"
            if padre_key not in comp_data['preguntas_con_padre']:
                padre_obj = lista_preg[0].padre if lista_preg else None
                comp_data['preguntas_con_padre'][padre_key] = {
                    'padre': padre_obj,
                    'preguntas': []
                }
            
            for preg in lista_preg:
                key = f"comp_{comp_id}_padre_{padre_id}_preg_{preg.id}"
                comp_data['preguntas_con_padre'][padre_key]['preguntas'].append({
                    "pregunta": preg,
                    "key": key,
                    "valor": valores_campos.get(key, ""),
                })
        
        componentes_con_preguntas.append(comp_data)

    # Controlar si hay componentes (excepto para observaciones)
    hay_componentes_reales = categoria != "observaciones" and any(comp for comp in componentes if comp is not None)

    return render(request, "revisar_subestacion.html", {
        "orden": orden,
        "subestacion": subestacion,
        "componentes_con_preguntas": componentes_con_preguntas,
        "categoria": categoria,
        "tipo_componente": tipo,
        "observaciones": valores_campos.get("observaciones_generales", ""),
        "hay_componentes": hay_componentes_reales,  # Para controlar en template
        "es_observaciones": categoria == "observaciones",  # Nueva variable
    })

# ==============================
#  Guardar definitivamente
# ==============================
def enviar_informe_final(request, orden_id):
    orden = get_object_or_404(OrdenSubestacion, pk=orden_id)
    subestacion = orden.id_subestacion

    respuestas_temporales = request.session.get("respuestas_temporales", {})
    if not respuestas_temporales:
        messages.error(request, "No hay respuestas para enviar.")
        return redirect("seleccionar_reporte", id=orden.id_orden)

    # 🔹 Obtener o crear la revisión única para esta orden
    revision, creada = RevisionSubestacion.objects.get_or_create(
        orden=orden,
        defaults={"subestacion": subestacion}
    )

    # 🔹 Todas las respuestas de esta orden
    respuestas_orden = respuestas_temporales.get(str(orden.id_orden), {})

    # 🔹 Guardar observaciones generales
    obs_post = request.POST.get("observaciones_generales", "").strip()
    revision.observaciones_generales = obs_post or respuestas_orden.get("observaciones_generales", "")
    revision.save()

    # 🔹 Eliminar respuestas viejas
    Respuesta.objects.filter(revision=revision).delete()


    # 🔹 Recorrer TODAS las categorías y respuestas guardadas
    for categoria, respuestas in respuestas_orden.items():
        if categoria == "observaciones_generales":
            continue

        for key, value in respuestas.items():
            if not value:
                continue

            try:
                parts = key.split('_')
                preg_id = None
                for i, part in enumerate(parts):
                    if part == 'preg' and i + 1 < len(parts):
                        preg_id = int(parts[i + 1])
                        break
                if not preg_id:
                    continue

                pregunta = Pregunta.objects.get(id=preg_id)
            except (ValueError, Pregunta.DoesNotExist):
                continue

            componente = None
            if key.startswith("comp_"):
                try:
                    comp_id = parts[1]
                    if comp_id != "obs_general":
                        componente = ComponenteSubestacion.objects.filter(
                            id_componente_sube=int(comp_id)
                        ).first()
                except (IndexError, ValueError):
                    pass

            Respuesta.objects.create(
                revision=revision,
                pregunta=pregunta,
                componente=componente,
                respuesta=value
            )

    # ==============================
    # 🔹 Crear histórico
    # ==============================
    HistoricoSubestacion.objects.create(
        subestacion=subestacion,
        orden=orden,
        observaciones_generales=revision.observaciones_generales
    )

    # ==============================
    # 🔹 CAMBIAR ESTADO DE LA ORDEN
    # ==============================
    orden.estado_orden = "pendiente_por_revisar"
    orden.save()

    # Limpiar sesión SOLO de esta orden
    if str(orden.id_orden) in request.session.get("respuestas_temporales", {}):
        del request.session["respuestas_temporales"][str(orden.id_orden)]
        request.session.modified = True

    messages.success(request, "Informe enviado y la orden quedó 'Pendiente por revisar'.")
    return redirect("ordenes_subestacion_operario")



# ==============================
#  Preguntas
# ==============================
def lista_preguntas(request):
    preguntas = Pregunta.objects.all()
    return render(request, "lista_preguntas.html", {"preguntas": preguntas})


def crear_pregunta(request):
    if request.method == "POST":
        form = PreguntaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Pregunta creada correctamente")
            return redirect("lista_preguntas")  # Ajusta este nombre según tu URL
    else:
        form = PreguntaForm()

    return render(request, "crear_pregunta.html", {"form": form})

def filtrar_padres(request):
    """Vista AJAX para filtrar preguntas padre por categoría"""
    categoria = request.GET.get('categoria')
    if categoria:
        try:
            padres = PreguntaPadre.objects.filter(categoria=categoria)
            options = '<option value="">---------</option>'
            for padre in padres:
                options += f'<option value="{padre.id}">{padre.texto}</option>'
            return JsonResponse({'options': options})
        except (ValueError, TypeError):
            return JsonResponse({'options': '<option value="">---------</option>'})
    
    return JsonResponse({'options': '<option value="">---------</option>'})


def eliminar_pregunta(request, id):
    pregunta = get_object_or_404(Pregunta, pk=id)
    if request.method == "POST":
        pregunta.delete()
        messages.success(request, " Pregunta eliminada correctamente")
        return redirect("lista_preguntas")
    return render(request, "eliminar_pregunta.html", {"pregunta": pregunta})


# ==============================
#  Subestaciones (operario)
# ==============================
def subestaciones_operario(request):
    subestaciones = Subestacion.objects.all()
    return render(request, "subestaciones_operario.html", {
        "subestaciones": subestaciones
    })


def seleccionar_reporte(request, id):
    orden = get_object_or_404(OrdenSubestacion, pk=id)
    subestacion = orden.id_subestacion

    if not subestacion:
        messages.error(request, "Esta orden no tiene una subestación asociada.")
        return redirect("lista_ordenes_operario")

    # Respuestas en sesión (solo de esta orden)
    respuestas = request.session.get("respuestas_temporales", {})
    respuestas_orden = respuestas.get(str(orden.id_orden), {})

    # Respuestas guardadas en BD
    respuestas_db = Respuesta.objects.filter(
        revision__orden=orden
    ).exists()

    # Mostrar botón si hay en sesión o BD
    tiene_respuestas = bool(respuestas_orden) or respuestas_db

    return render(request, "seleccionar_reporte.html", {
        "orden": orden,
        "subestacion": subestacion,
        "tiene_respuestas": tiene_respuestas,
    })


def resumen_revision(request, orden_id):
    revision = get_object_or_404(RevisionSubestacion, orden_id=orden_id)
    subestacion = revision.subestacion

    # Obtener todas las respuestas de esta revisión con sus relaciones
    respuestas = Respuesta.objects.filter(revision=revision).select_related("pregunta", "componente", "pregunta__padre")

    # Estructura mejorada para el resumen
    resumen = {}
    
    for resp in respuestas:
        categoria = resp.pregunta.categoria
        componente = resp.componente  # Esto ya es el objeto ComponenteSubestacion
        
        # Inicializar categoría si no existe
        if categoria not in resumen:
            resumen[categoria] = {}
        
        # Usar el nombre del componente o "General" si no hay componente
        if componente:
            comp_key = f"{componente.nombre_componente} ({componente.get_tipo_display()})"
        else:
            comp_key = "General"
        
        # Inicializar lista de respuestas para este componente
        if comp_key not in resumen[categoria]:
            resumen[categoria][comp_key] = []
        
        # Agregar la respuesta
        resumen[categoria][comp_key].append(resp)

    # Si no hay respuestas, mostrar mensaje
    if not respuestas.exists():
        messages.info(request, "No hay respuestas registradas para esta revisión.")

    return render(request, "resumen_revision.html", {
        "revision": revision,
        "subestacion": subestacion,
        "resumen": resumen,
        "total_respuestas": respuestas.count(),
    })


# ==============================
#  Órdenes
# ==============================
def crear_orden_subestacion(request):
    if request.method == "POST":
        form = OrdenSubestacionForm(request.POST)
        if form.is_valid():
            orden = form.save(commit=False)
            orden.estado_orden = "pendiente"
            orden.save()
            return redirect("lista_ordenes_subestacion")
    else:
        form = OrdenSubestacionForm()

    return render(request, "crear_orden_subestacion.html", {"form": form})


def lista_ordenes_subestacion(request):
    ordenes = OrdenSubestacion.objects.select_related("id_subestacion").all().order_by("-fecha")

    # Creamos un diccionario {id_orden: revision}
    revisiones = {
        rev.orden.id_orden: rev
        for rev in RevisionSubestacion.objects.select_related("orden")
    }

    return render(request, "lista_ordenes_subestacion.html", {
        "ordenes": ordenes,
        "revisiones": revisiones
    })


def lista_ordenes_operario(request):
    ordenes = OrdenSubestacion.objects.all().select_related("id_subestacion")

    ordenes_context = []
    for orden in ordenes:
        tiene_revision = hasattr(orden, "revision")
        ordenes_context.append({
            "id": orden.id_orden,
            "numero": orden.numero_orden_sube,
            "descripcion": orden.descripcion_orden_sube,
            "estado": orden.estado_orden,
            "fecha": orden.fecha,
            "subestacion": orden.id_subestacion.nombre,
            "tiene_revision": tiene_revision,
        })

    return render(request, "ordenes_subestacion_operario.html", {
        "ordenes": ordenes_context
    })

def crear_pregunta_padre(request):
    if request.method == "POST":
        form = PreguntaPadreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pregunta padre creada correctamente ✅")
            return redirect("lista_preguntas")  # 👈 ajusta al nombre de tu url de listado
    else:
        form = PreguntaPadreForm()

    return render(request, "crear_pregunta_padre.html", {"form": form})


# Eliminar
def eliminar_pregunta_padre(request, id):
    pregunta = get_object_or_404(PreguntaPadre, id=id)

    if request.method == "POST":
        pregunta.delete()
        messages.success(request, "Pregunta padre eliminada correctamente 🗑️")
        return redirect("lista_preguntas")

    return render(request, "eliminar_pregunta_padre.html", {"pregunta": pregunta})    

def historico_subestacion(request, subestacion_id):
    # 1️⃣ Obtener la subestación específica (o mostrar error 404 si no existe)
    # ------------------------------------------------------------------------
    # Se busca en la base de datos el objeto Subestacion con el ID recibido.
    # Si no se encuentra, Django lanza automáticamente un error 404.
    subestacion = get_object_or_404(Subestacion, id=subestacion_id)

    # 2️⃣ Consultar los registros históricos asociados a esa subestación
    # ------------------------------------------------------------------------
    # Filtra los objetos HistoricoSubestacion que pertenezcan a la subestación.
    # 'select_related("orden")' permite traer también el objeto 'orden' asociado
    # en la misma consulta (optimiza rendimiento evitando consultas repetidas).
    # Finalmente, los ordena de forma descendente por fecha (más reciente primero).
    historicos = (
        HistoricoSubestacion.objects.filter(subestacion=subestacion)
        .select_related("orden")
        .order_by("-fecha")
    )

    # 3️⃣ Preparar una lista que contenga los datos combinados de cada histórico
    # ------------------------------------------------------------------------
    # Para cada histórico, se busca la revisión y sus respuestas (si existen).
    datos = []

    for h in historicos:
        # 3.1 Buscar si existe una revisión asociada a la orden del histórico actual
        # --------------------------------------------------------------------------
        # Cada registro histórico tiene una 'orden'. Si esa orden fue revisada,
        # habrá una entrada en 'RevisionSubestacion' vinculada a esa orden.
        revision = RevisionSubestacion.objects.filter(orden=h.orden).first()

        # 3.2 Inicializar la lista de respuestas vacía
        respuestas = []

        # 3.3 Si la revisión existe, consultar las respuestas vinculadas a ella
        # ----------------------------------------------------------------------
        # Se buscan las respuestas relacionadas con esa revisión específica.
        # 'select_related("pregunta", "componente")' hace que también se traigan
        # los objetos relacionados 'pregunta' y 'componente' en la misma consulta.
        if revision:
            respuestas = Respuesta.objects.filter(revision=revision).select_related("pregunta", "componente")

        # 3.4 Guardar toda la información combinada en una sola estructura
        # -----------------------------------------------------------------
        # Se agrega un diccionario con el histórico, su revisión (si hay)
        # y las respuestas obtenidas, para luego pasarlo a la plantilla.
        datos.append({
            "historico": h,
            "revision": revision,
            "respuestas": respuestas
        })

    # 4️⃣ Renderizar la plantilla con toda la información procesada
    # ------------------------------------------------------------------------
    # Se envía a la vista HTML:
    #   - La subestación seleccionada
    #   - La lista de 'datos', que contiene cada histórico con su revisión y respuestas
    return render(request, "historico_subestacion.html", {
        "subestacion": subestacion,
        "datos": datos
    })






from django.shortcuts import render
from django.urls import reverse
from django.db.models import Count
from .models import Reconectador, Comunicacion

def pruebapotly(request):
    import pandas as pd

    # 1️⃣ Totales generales
    total_nodos = Reconectador.objects.values('id_nodo').distinct().count()
    total_subestaciones = Reconectador.objects.values('id_nodo__id_subestacion').distinct().count()
    total_recos = Reconectador.objects.count()
    total_comunicaciones = Comunicacion.objects.count()

    # 2️⃣ Datos para gráficos
    recos_por_subestacion = (
        Reconectador.objects
        .values('id_nodo__id_subestacion__nombre')
        .annotate(total=Count('id_reco'))
        .order_by('id_nodo__id_subestacion__nombre')
    )
    subestaciones = [r['id_nodo__id_subestacion__nombre'] for r in recos_por_subestacion]
    recos_subestacion = [r['total'] for r in recos_por_subestacion]

    comunicaciones_por_estado = (
        Comunicacion.objects
        .values('estado')
        .annotate(total=Count('id_comunicacion'))
        .order_by('estado')
    )
    estados = [r['estado'] if r['estado'] else 'Sin estado' for r in comunicaciones_por_estado]
    total_por_estado = [r['total'] for r in comunicaciones_por_estado]

    actividad_comunicaciones = (
        Comunicacion.objects
        .values('estado_actividad')
        .annotate(total=Count('id_comunicacion'))
        .order_by('estado_actividad')
    )
    actividad_labels = [
        r['estado_actividad'] if r['estado_actividad'] not in [None, '', 'nan'] else 'Sin dato'
        for r in actividad_comunicaciones
    ]
    actividad_totales = [r['total'] for r in actividad_comunicaciones]

    modems_por_tecnologia = (
        Comunicacion.objects
        .values('tecnologia')
        .annotate(total=Count('id_comunicacion'))
        .order_by('tecnologia')
    )
    tecnologias = [m['tecnologia'] if m['tecnologia'] else 'Sin dato' for m in modems_por_tecnologia]
    total_tecnologias = [m['total'] for m in modems_por_tecnologia]

    pendiente_operacion = (
        Comunicacion.objects
        .filter(estado__iexact="pendiente operacion")
        .values('estado_actividad')
        .annotate(total=Count('id_comunicacion'))
        .order_by('estado_actividad')
    )
    pendiente_labels = [
        p['estado_actividad'] if p['estado_actividad'] not in [None, '', 'nan'] else 'Sin dato'
        for p in pendiente_operacion
    ]
    pendiente_totales = [p['total'] for p in pendiente_operacion]

    ri_obsoleto = (
        Comunicacion.objects
        .filter(estado__iexact="RI OBSOLETO")
        .values('estado_actividad')
        .annotate(total=Count('id_comunicacion'))
        .order_by('estado_actividad')
    )
    ri_obsoleto_labels = [
        r['estado_actividad'] if r['estado_actividad'] not in [None, '', 'nan'] else 'Sin dato'
        for r in ri_obsoleto
    ]
    ri_obsoleto_totales = [r['total'] for r in ri_obsoleto]

    # ================================
    #   *** FUNCIÓN CORREGIDA ***
    # ================================
    def crear_grafico(x, y, titulo):
        df = pd.DataFrame({
            "categoria": x,
            "valor": y
        })

        fig = px.bar(
            df,
            x="categoria",
            y="valor",
            title=titulo,
            text="valor",
            color="categoria",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )

        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(
            height=550,
            margin=dict(t=80, b=100, l=50, r=30),
            xaxis_tickangle=-35,
            paper_bgcolor='#fff',
            plot_bgcolor='#f9fafb',
            font=dict(size=13, color='#2c3e50', family='Segoe UI'),
            title_font=dict(size=20, color='#2c3e50'),
        )
        return fig.to_html(full_html=False)

    # ===============================
    #   GENERAR GRÁFICOS
    # ===============================
    grafico1 = crear_grafico(subestaciones, recos_subestacion, "Recos por Subestación")
    grafico2 = crear_grafico(estados, total_por_estado, "Estado Comunicación")
    grafico3 = crear_grafico(actividad_labels, actividad_totales, "Actividad Comunicaciones")
    grafico4 = crear_grafico(tecnologias, total_tecnologias, "Módems por Tecnología")
    grafico5 = crear_grafico(pendiente_labels, pendiente_totales, "Pendiente Mantenimiento")
    grafico6 = crear_grafico(ri_obsoleto_labels, ri_obsoleto_totales, "RI Obsoleto")

    # 4️⃣ Control del botón "volver"
    origen_param = request.GET.get("from", "mantenimiento")
    try:
        url_origen = reverse(origen_param)
    except:
        url_origen = reverse("mantenimiento")

    return render(request, 'plotlyprueba.html', {
        'total_nodos': total_nodos,
        'total_subestaciones': total_subestaciones,
        'total_recos': total_recos,
        'total_comunicaciones': total_comunicaciones,
        'grafico1': grafico1,
        'grafico2': grafico2,
        'grafico3': grafico3,
        'grafico4': grafico4,
        'grafico5': grafico5,
        'grafico6': grafico6,
        'url_origen': url_origen,
    })




def mapa_ordenes(request):
    # Obtener todos los nodos con coordenadas
    nodos = Nodo.objects.filter(latitud__isnull=False, longitud__isnull=False)
    
    # Preparar datos para el template
    nodos_data = []
    for nodo in nodos:
        nodos_data.append({
            'id': nodo.id_nodo,
            'nombre': nodo.nodo,
            'direccion': nodo.direccion,
            'latitud': float(nodo.latitud),
            'longitud': float(nodo.longitud),
            'circuito1': nodo.circuito1 or 'N/A',
            'circuito2': nodo.circuito2 or 'N/A',
            'clasificacion': nodo.clasificacion or 'N/A',
            'nt': nodo.nt or 'N/A',
            'subestacion': str(nodo.id_subestacion) if nodo.id_subestacion else 'N/A'
        })
    
    context = {
        'nodos': json.dumps(nodos_data),
        'centro_cali': [3.4516, -76.5320],
        'total_nodos': nodos.count()
    }
    
    return render(request, 'mapa_ordenes.html', context)

def grafico_fallas(request):
    # === Parámetros GET ===
    rango = request.GET.get('rango', '15d')  # 15d, 3m, 12m
    falla_seleccionada = request.GET.get('falla', '')

    # === Determinar rango de fechas ===
    fecha_fin = timezone.now().date()
    if rango == '3m':
        fecha_inicio = fecha_fin - timedelta(days=90)
    elif rango == '12m':
        fecha_inicio = fecha_fin - timedelta(days=365)
    else:
        fecha_inicio = fecha_fin - timedelta(days=15)

    # === Filtro base ===
    informes = InformeReco.objects.filter(
        inicio_actividad__date__range=(fecha_inicio, fecha_fin)
    )

    if falla_seleccionada:
        informes = informes.filter(falla_identificada=falla_seleccionada)

    informes = informes.values('falla_identificada', 'inicio_actividad')

    # === Crear DataFrame ===
    if not informes.exists():
        grafico = "<p class='text-center text-muted'>No hay datos disponibles para el rango seleccionado.</p>"
    else:
        df = pd.DataFrame(informes)

        # Agrupar por falla
        df_group = df.groupby('falla_identificada').size().reset_index(name='conteo')

        # === Crear gráfico con Plotly ===
        fig = px.bar(
            df_group,
            x='falla_identificada',
            y='conteo',
            title=f"Fallas identificadas ({fecha_inicio} → {fecha_fin})",
            text='conteo',
            color='falla_identificada'
        )
        fig.update_layout(
            xaxis_title="Tipo de Falla",
            yaxis_title="Cantidad de casos",
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_x=0.5
        )
        grafico = plot(fig, output_type='div')

    # === Opciones de fallas (como en tu select HTML) ===
    opciones_fallas = [
        ('falta_tension_ac', 'Falta tensión AC'),
        ('modem_apagado', 'Modem apagado'),
        ('display_no_prende', 'Display caja de control no prende'),
        ('breaker_abierto', 'Breaker de alimentación AC abierto'),
        ('fuente_dc_apagada', 'Fuente externa DC apagada'),
        ('caja_bloqueada', 'Caja de control bloqueada'),
        ('falta_antena', 'Falta antena'),
        ('antena_caida', 'Antena caída'),
        ('modem_no_comunica', 'Modem no comunica'),
        ('falla_fibra', 'Falla en fibra óptica'),
        ('desconocida', 'Desconocida'),
    ]

    return render(request, 'grafico_fallas.html', {
        'grafico': grafico,
        'rango': rango,
        'falla_seleccionada': falla_seleccionada,
        'opciones_fallas': opciones_fallas,
    })

def historial_nodo(request):
    query = request.GET.get('q')
    nodo = None
    informes = []
    grafico_html = None

    if query:
        # Buscar por el nombre real del nodo
        nodo = Nodo.objects.filter(nodo__icontains=query).first()

        if nodo:
            # Buscar informes relacionados con ese nodo
            informes = InformeReco.objects.filter(orden__id_nodo=nodo).order_by('-inicio_actividad')

            if informes.exists():
                # Crear DataFrame con fallas
                df = pd.DataFrame(list(informes.values('falla_identificada')))
                df['falla_identificada'] = df['falla_identificada'].fillna('No especificada')

                conteo = df['falla_identificada'].value_counts().reset_index()
                conteo.columns = ['Falla', 'Cantidad']

                # Gráfico de barras Plotly
                fig = px.bar(
                    conteo,
                    x='Falla',
                    y='Cantidad',
                    text='Cantidad',
                    color='Falla',
                    title=f"Fallas registradas en nodo {nodo.nodo}"
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(xaxis_title="Tipo de Falla", yaxis_title="Cantidad", title_x=0.5)

                grafico_html = fig.to_html(full_html=False)

    return render(request, 'nodo_busqueda.html', {
        'nodo': nodo,
        'informes': informes,
        'query': query,
        'grafico_html': grafico_html,
    })    

def registrar_usuario(request):
    if request.method == "POST":
        form = UsuarioRegistroForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            nombre_completo = form.cleaned_data["nombre_completo"]
            cc = form.cleaned_data["cc"]
            rol = form.cleaned_data["rol"]

            # Crear usuario del sistema - GUARDANDO EL EMAIL TAMBIÉN
            user = User.objects.create_user(
                username=username, 
                password=password,
                email=username  # ← ESTA LÍNEA ES LA CLAVE
            )

            # Crear trabajador vinculado
            Trabajador.objects.create(
                user=user,
                nombre_completo=nombre_completo,
                cc=cc,
                id_rol=rol
            )

            messages.success(request, f"Usuario '{username}' creado exitosamente con rol '{rol.nombre}'.")
            return redirect("mantenimiento")  # o donde quieras redirigir
    else:
        form = UsuarioRegistroForm()

    return render(request, "crear_usuario.html", {"form": form})

def user_role_context(request):
    if not request.user.is_authenticated:
        return {'user_role': None}

    try:
        trabajador = Trabajador.objects.select_related('rol').get(user=request.user)
        user_role = trabajador.rol.nombre.lower()
    except Trabajador.DoesNotExist:
        user_role = None

    return {'user_role': user_role}    

def ver_ruta_nodo(request):
    nodo_buscar = request.GET.get("nodo", None)
    nodo_obj = None

    if nodo_buscar:
        nodo_obj = get_object_or_404(Nodo, nodo=nodo_buscar)

    return render(request, "ver_ruta_nodo.html", {
        "nodo": nodo_obj,
    })

def dashboard_estadisticas_completo(request):
    # ================================
    # 0️⃣ PALETA DE COLORES EMCALI
    # ================================
    COLORES_EMCALI = {
        'verde_principal': '#00A859',
        'verde_secundario': '#00C46C',
        'verde_claro': '#E6F7EF',
        'azul_principal': '#0057B8',
        'azul_secundario': '#0072E3',
        'azul_claro': '#E6F0FF',
        'amarillo': '#FFD100',
        'rojo': '#E30613',
        'gris_oscuro': '#333333',
        'gris_medio': '#666666',
        'gris_claro': '#F5F5F5'
    }
    
    # ================================
    # 1️⃣ DATOS GENERALES (de pruebapotly)
    # ================================
    
    # Totales generales
    total_nodos = Reconectador.objects.values('id_nodo').distinct().count()
    total_subestaciones = Reconectador.objects.values('id_nodo__id_subestacion').distinct().count()
    total_recos = Reconectador.objects.count()
    total_comunicaciones = Comunicacion.objects.count()

    # Datos para gráficos de pruebapotly
    recos_por_subestacion = (
        Reconectador.objects
        .values('id_nodo__id_subestacion__nombre')
        .annotate(total=Count('id_reco'))
        .order_by('id_nodo__id_subestacion__nombre')
    )
    subestaciones = [r['id_nodo__id_subestacion__nombre'] for r in recos_por_subestacion]
    recos_subestacion = [r['total'] for r in recos_por_subestacion]

    comunicaciones_por_estado = (
        Comunicacion.objects
        .values('estado')
        .annotate(total=Count('id_comunicacion'))
        .order_by('estado')
    )
    estados = [r['estado'] if r['estado'] else 'Sin estado' for r in comunicaciones_por_estado]
    total_por_estado = [r['total'] for r in comunicaciones_por_estado]

    actividad_comunicaciones = (
        Comunicacion.objects
        .values('estado_actividad')
        .annotate(total=Count('id_comunicacion'))
        .order_by('estado_actividad')
    )
    actividad_labels = [
        r['estado_actividad'] if r['estado_actividad'] not in [None, '', 'nan'] else 'Sin dato'
        for r in actividad_comunicaciones
    ]
    actividad_totales = [r['total'] for r in actividad_comunicaciones]

    modems_por_tecnologia = (
        Comunicacion.objects
        .values('tecnologia')
        .annotate(total=Count('id_comunicacion'))
        .order_by('tecnologia')
    )
    tecnologias = [m['tecnologia'] if m['tecnologia'] else 'Sin dato' for m in modems_por_tecnologia]
    total_tecnologias = [m['total'] for m in modems_por_tecnologia]

    pendiente_operacion = (
        Comunicacion.objects
        .filter(estado__iexact="pendiente operacion")
        .values('estado_actividad')
        .annotate(total=Count('id_comunicacion'))
        .order_by('estado_actividad')
    )
    pendiente_labels = [
        p['estado_actividad'] if p['estado_actividad'] not in [None, '', 'nan'] else 'Sin dato'
        for p in pendiente_operacion
    ]
    pendiente_totales = [p['total'] for p in pendiente_operacion]

    ri_obsoleto = (
        Comunicacion.objects
        .filter(estado__iexact="RI OBSOLETO")
        .values('estado_actividad')
        .annotate(total=Count('id_comunicacion'))
        .order_by('estado_actividad')
    )
    ri_obsoleto_labels = [
        r['estado_actividad'] if r['estado_actividad'] not in [None, '', 'nan'] else 'Sin dato'
        for r in ri_obsoleto
    ]
    ri_obsoleto_totales = [r['total'] for r in ri_obsoleto]

    # ================================
    # 2️⃣ DATOS ESPECÍFICOS EMCALI (de grafico_comunicaciones)
    # ================================
    
    ESTADOS_VALIDOS = [
        "OPERATIVO",
        "Pendiente Mantenimiento",
        "Pendiente Operacion",
        "Pendiente Telco",
        "NA",
    ]

    # Filtrar comunicaciones por responsable EMCALI
    comunicaciones_emcali = Comunicacion.objects.filter(
        id_reco__responsable__iexact="emcali",
        estado__in=ESTADOS_VALIDOS
    )

    conteo_total_emcali = comunicaciones_emcali.count()

    # Histograma EMCALI
    data_emcali = [{"estado": c.estado} for c in comunicaciones_emcali]
    
    if not data_emcali:
        chart_emcali_html = "<h4>No hay datos EMCALI para mostrar.</h4>"
    else:
        fig_emcali = px.histogram(
            data_emcali,
            x="estado",
            color="estado",
            title="Estados de Comunicación - Responsable EMCALI",
            text_auto=True,
            color_discrete_sequence=[
                COLORES_EMCALI['verde_principal'],  # OPERATIVO
                COLORES_EMCALI['amarillo'],         # Pendiente Mantenimiento
                COLORES_EMCALI['rojo'],             # Pendiente Operacion
                COLORES_EMCALI['azul_principal'],   # Pendiente Telco
                COLORES_EMCALI['gris_medio']        # NA
            ]
        )
        fig_emcali.update_layout(
            autosize=True,
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='white',
            plot_bgcolor=COLORES_EMCALI['gris_claro'],
            font=dict(color=COLORES_EMCALI['gris_oscuro']),
            title_font=dict(color=COLORES_EMCALI['azul_principal'])
        )
        chart_emcali_html = fig_emcali.to_html(full_html=False)

    # Torta EMCALI
    ESTADOS_SIN = ["Pendiente Mantenimiento", "Pendiente Operacion", "Pendiente Telco"]
    sin_com_emcali = comunicaciones_emcali.filter(estado__in=ESTADOS_SIN).count()
    comunicados_emcali = conteo_total_emcali - sin_com_emcali

    data_torta_emcali = {
        "categoria": ["Comunicados", "Sin Comunicación"],
        "cantidad": [comunicados_emcali, sin_com_emcali]
    }

    fig_torta_emcali = px.pie(
        data_torta_emcali,
        names="categoria",
        values="cantidad",
        title="Comunicación General - EMCALI",
        color_discrete_sequence=[COLORES_EMCALI['verde_principal'], COLORES_EMCALI['rojo']]
    )
    fig_torta_emcali.update_traces(textinfo="label+value+percent")
    fig_torta_emcali.update_layout(
        autosize=True,
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='white',
        font=dict(color=COLORES_EMCALI['gris_oscuro']),
        title_font=dict(color=COLORES_EMCALI['azul_principal'])
    )
    torta_emcali_html = fig_torta_emcali.to_html(full_html=False)

    # ================================
    # 3️⃣ DATOS DE FALLAS (de grafico_fallas)
    # ================================
    
    # Parámetros GET para fallas
    rango = request.GET.get('rango', '15d')
    falla_seleccionada = request.GET.get('falla', '')

    # Determinar rango de fechas para fallas
    fecha_fin = timezone.now().date()
    if rango == '3m':
        fecha_inicio = fecha_fin - timedelta(days=90)
    elif rango == '12m':
        fecha_inicio = fecha_fin - timedelta(days=365)
    else:
        fecha_inicio = fecha_fin - timedelta(days=15)

    # Filtro base para fallas
    informes = InformeReco.objects.filter(
        inicio_actividad__date__range=(fecha_inicio, fecha_fin)
    )

    if falla_seleccionada:
        informes = informes.filter(falla_identificada=falla_seleccionada)

    informes = informes.values('falla_identificada', 'inicio_actividad')

    # Crear gráfico de fallas
    if not informes.exists():
        grafico_fallas_html = "<p class='text-center text-muted'>No hay datos de fallas disponibles para el rango seleccionado.</p>"
    else:
        df = pd.DataFrame(informes)
        df_group = df.groupby('falla_identificada').size().reset_index(name='conteo')

        fig_fallas = px.bar(
            df_group,
            x='falla_identificada',
            y='conteo',
            title=f"Fallas identificadas ({fecha_inicio} → {fecha_fin})",
            text='conteo',
            color='falla_identificada',
            color_discrete_sequence=[
                COLORES_EMCALI['rojo'], COLORES_EMCALI['amarillo'], COLORES_EMCALI['azul_principal'],
                COLORES_EMCALI['verde_principal'], COLORES_EMCALI['gris_medio'], COLORES_EMCALI['azul_secundario'],
                COLORES_EMCALI['verde_secundario'], COLORES_EMCALI['rojo'], COLORES_EMCALI['amarillo'],
                COLORES_EMCALI['azul_principal'], COLORES_EMCALI['gris_oscuro']
            ]
        )
        fig_fallas.update_layout(
            xaxis_title="Tipo de Falla",
            yaxis_title="Cantidad de casos",
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
            title_x=0.5,
            height=500,
            font=dict(color=COLORES_EMCALI['gris_oscuro']),
            title_font=dict(color=COLORES_EMCALI['azul_principal'])
        )
        grafico_fallas_html = plot(fig_fallas, output_type='div')

    # Opciones de fallas
    opciones_fallas = [
        ('falta_tension_ac', 'Falta tensión AC'),
        ('modem_apagado', 'Modem apagado'),
        ('display_no_prende', 'Display caja de control no prende'),
        ('breaker_abierto', 'Breaker de alimentación AC abierto'),
        ('fuente_dc_apagada', 'Fuente externa DC apagada'),
        ('caja_bloqueada', 'Caja de control bloqueada'),
        ('falta_antena', 'Falta antena'),
        ('antena_caida', 'Antena caída'),
        ('modem_no_comunica', 'Modem no comunica'),
        ('falla_fibra', 'Falla en fibra óptica'),
        ('desconocida', 'Desconocida'),
    ]

    # ================================
    # 4️⃣ FUNCIÓN PARA GRÁFICOS (de pruebapotly)
    # ================================
    
    def crear_grafico(x, y, titulo):
        df = pd.DataFrame({
            "categoria": x,
            "valor": y
        })

        fig = px.bar(
            df,
            x="categoria",
            y="valor",
            title=titulo,
            text="valor",
            color="categoria",
            color_discrete_sequence=[
                COLORES_EMCALI['verde_principal'], COLORES_EMCALI['azul_principal'], 
                COLORES_EMCALI['amarillo'], COLORES_EMCALI['rojo'], COLORES_EMCALI['gris_medio'],
                COLORES_EMCALI['verde_secundario'], COLORES_EMCALI['azul_secundario']
            ]
        )

        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(
            height=550,
            margin=dict(t=80, b=100, l=50, r=30),
            xaxis_tickangle=-35,
            paper_bgcolor='white',
            plot_bgcolor=COLORES_EMCALI['gris_claro'],
            font=dict(size=13, color=COLORES_EMCALI['gris_oscuro'], family='Segoe UI'),
            title_font=dict(size=20, color=COLORES_EMCALI['azul_principal']),
        )
        return fig.to_html(full_html=False)

    # Generar gráficos de pruebapotly
    grafico1 = crear_grafico(subestaciones, recos_subestacion, "Recos por Subestación")
    grafico2 = crear_grafico(estados, total_por_estado, "Estado Comunicación")
    grafico3 = crear_grafico(actividad_labels, actividad_totales, "Actividad Comunicaciones")
    grafico4 = crear_grafico(tecnologias, total_tecnologias, "Módems por Tecnología")
    grafico5 = crear_grafico(pendiente_labels, pendiente_totales, "Pendiente Mantenimiento")
    grafico6 = crear_grafico(ri_obsoleto_labels, ri_obsoleto_totales, "RI Obsoleto")

    # 5️⃣ Control del botón "volver"
    origen_param = request.GET.get("from", "mantenimiento")
    try:
        url_origen = reverse(origen_param)
    except:
        url_origen = reverse("mantenimiento")

    return render(request, 'dashboard_completo.html', {
        # Totales generales
        'total_nodos': total_nodos,
        'total_subestaciones': total_subestaciones,
        'total_recos': total_recos,
        'total_comunicaciones': total_comunicaciones,
        
        # Gráficos generales
        'grafico1': grafico1,
        'grafico2': grafico2,
        'grafico3': grafico3,
        'grafico4': grafico4,
        'grafico5': grafico5,
        'grafico6': grafico6,
        
        # Datos EMCALI
        'grafico_emcali': chart_emcali_html,
        'torta_emcali': torta_emcali_html,
        'conteo_total_emcali': conteo_total_emcali,
        'comunicados_emcali': comunicados_emcali,
        'sin_com_emcali': sin_com_emcali,
        
        # Datos de Fallas
        'grafico_fallas': grafico_fallas_html,
        'rango': rango,
        'falla_seleccionada': falla_seleccionada,
        'opciones_fallas': opciones_fallas,
        'fecha_inicio_fallas': fecha_inicio,
        'fecha_fin_fallas': fecha_fin,
        
        # Colores EMCALI para el template
        'colores_emcali': COLORES_EMCALI,
        
        # Navegación
        'url_origen': url_origen,
    })    
def solicitar_codigo(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No existe un usuario con ese correo.")
            return redirect("solicitar_codigo")

        # Generar código
        codigo = str(random.randint(100000, 999999))

        # Guardarlo
        CodigoRecuperacion.objects.update_or_create(
            user=user,
            defaults={"codigo": codigo}
        )

        # Enviar correo
        send_mail(
            "Código de recuperación de contraseña",
            f"Tu código es: {codigo}",
            "tucorreo@gmail.com",
            [email],
            fail_silently=False,
        )

        messages.success(request, "Se envió un código a tu correo.")
        return redirect("verificar_codigo")

    return render(request, "solicitar_codigo.html")    

def verificar_codigo(request):
    if request.method == "POST":
        email = request.POST.get("email")
        codigo = request.POST.get("codigo")

        try:
            user = User.objects.get(email=email)
            registro = CodigoRecuperacion.objects.get(user=user)
        except:
            messages.error(request, "Correo o código incorrecto.")
            return redirect("verificar_codigo")

        if registro.codigo == codigo:
            request.session["recuperar_user_id"] = user.id
            return redirect("cambiar_contrasena")

        messages.error(request, "Código incorrecto.")
        return redirect("verificar_codigo")

    return render(request, "verificar_codigo.html")

from django.contrib.auth import update_session_auth_hash

def cambiar_contrasena(request):
    user_id = request.session.get("recuperar_user_id")

    if not user_id:
        return redirect("solicitar_codigo")

    user = User.objects.get(id=user_id)

    if request.method == "POST":
        nueva = request.POST.get("nueva")
        confirmar = request.POST.get("confirmar")

        if nueva != confirmar:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("cambiar_contrasena")

        user.set_password(nueva)
        user.save()
        CodigoRecuperacion.objects.filter(user=user).delete()
        del request.session["recuperar_user_id"]

        messages.success(request, "Contraseña cambiada correctamente.")
        return redirect("login")

    return render(request, "cambiar_contrasena.html")

from django.shortcuts import render
from django.db.models import Q
from .models import Nodo

def buscar_nodos(request):
    nodos = None
    query = ""

    # Lista de nodos para autocompletar
    nodos_lista = Nodo.objects.all().values('nodo').order_by('nodo')

    if 'q' in request.GET:
        query = request.GET.get('q')

        # Buscar por nodo, dirección, circuito o clasificación
        nodos = Nodo.objects.filter(
            Q(nodo__icontains=query) |
            Q(direccion__icontains=query) |
            Q(circuito1__icontains=query) |
            Q(circuito2__icontains=query) |
            Q(clasificacion__icontains=query)
        ).select_related('id_subestacion')

    # Procesar las coordenadas para reemplazar comas por puntos
    if nodos:
        for nodo in nodos:
            if nodo.latitud:
                nodo.latitud_processed = str(nodo.latitud).replace(',', '.')
            if nodo.longitud:
                nodo.longitud_processed = str(nodo.longitud).replace(',', '.')

    return render(request, 'buscar_nodos.html', {
        'nodos': nodos,
        'query': query,
        'nodos_lista': nodos_lista
    })