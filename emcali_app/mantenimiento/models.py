from django.db import models
from django.contrib.auth.models import User
class Subestacion(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre
class ComponenteSubestacion(models.Model):
    CIRCUITO = "circuito"
    TRANSFORMADOR = "transformador"
    SERVICIOS = "servicios"

    TIPOS = [
        (CIRCUITO, "Circuito"),
        (TRANSFORMADOR, "Transformador"),
        (SERVICIOS, "Servicios Auxiliares"),
    ]

    id_componente_sube = models.AutoField(primary_key=True)
    nombre_componente = models.CharField(max_length=100) 
    subestacion = models.ForeignKey(
        Subestacion,
        on_delete=models.CASCADE,
        related_name="componentes"
    )
    tipo = models.CharField(max_length=20, choices=TIPOS, default=CIRCUITO)  # 👈 Nuevo campo

    def __str__(self):
        return f"{self.nombre_componente} ({self.get_tipo_display()} - {self.subestacion.nombre})"


class Subestacion_comu_informe(models.Model):
    orden = models.ForeignKey('Orden', on_delete=models.CASCADE)

    hora_inicio = models.DateTimeField()
    trabajo_realizado_sub_comu = models.TextField()
    otras_observaciones = models.TextField(blank=True, null=True)  # <- útil que no sea obligatorio
    hora_cierre = models.DateTimeField(null=True, blank=True)  # <- por si aún no se ha cerrado

    longitud_sub = models.DecimalField(max_digits=12, decimal_places=9, null=True, blank=True)
    latitud_sub = models.DecimalField(max_digits=12, decimal_places=9, null=True, blank=True)


    def __str__(self):
        return f"Informe Subestación-Comu #{self.id} - Orden {self.orden.n_orden}"

class PreguntaPadre(models.Model):
    texto = models.CharField(max_length=200)
    categoria = models.CharField(
        max_length=30,
        choices=[
            ("bahia/interruptor", "Inspecciones Bahía"),
            ("transformador", "Inspección Transformador"),
            ("servicios", "Servicios Auxiliares"),
            ("observaciones", "Observaciones Generales"),  
        ],
        default="bahia"
    )

class Pregunta(models.Model):
    TEXTO = "texto"
    OPCION = "opcion"

    TIPOS = [
        (TEXTO, "Texto libre"),
        (OPCION, "Bien/Mal"),
    ]

    texto = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPOS, default=TEXTO)
    categoria = models.CharField(
        max_length=30,
        choices=[
            ("bahia", "Inspecciones Bahía"),
            ("transformador", "Inspección Transformador"),
            ("servicios", "Servicios Auxiliares"),
            ("observaciones", "Observaciones Generales"),  # 👈 NUEVA CATEGORÍA
        ],
        default="bahia"
    )

    # 🔹 Relación opcional con un padre
    padre = models.ForeignKey(
        PreguntaPadre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subpreguntas"
    )

    def __str__(self):
        padre_txt = f" → {self.padre.texto}" if self.padre else ""
        return f"[{self.get_categoria_display()}]{padre_txt} - {self.texto}"


class RevisionSubestacion(models.Model):
    subestacion = models.ForeignKey("Subestacion", on_delete=models.CASCADE)
    orden = models.OneToOneField(
        "OrdenSubestacion",
        on_delete=models.CASCADE,
        related_name="revision",
        null=True, blank=True
    )  # 👈 relación directa
    fecha = models.DateTimeField(auto_now_add=True)
    observaciones_generales = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Revisión {self.subestacion.nombre} - {self.fecha}"



class Respuesta(models.Model):
    revision = models.ForeignKey(RevisionSubestacion, on_delete=models.CASCADE)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    componente = models.ForeignKey(
        ComponenteSubestacion,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="respuestas"
    )
    respuesta = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.pregunta.texto} ({self.componente}): {self.respuesta}"



class Nodo(models.Model):
    id_nodo = models.AutoField(primary_key=True)
    nodo = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    longitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    circuito1 = models.CharField(max_length=100, blank=True, null=True)
    circuito2 = models.CharField(max_length=100, blank=True, null=True)
    clasificacion = models.CharField(max_length=100, blank=True, null=True)
    nt = models.CharField(max_length=50, blank=True, null=True)
    id_subestacion = models.ForeignKey(Subestacion, on_delete=models.CASCADE)

    def __str__(self):
        return f"Nodo {self.nodo}"
    


class Reconectador(models.Model):
    id_reco = models.AutoField(primary_key=True)
    activo_reco = models.IntegerField(default=0, null=True, blank=True)
    sn_activo = models.CharField(max_length=100, null=True, blank=True)
    n_equipo = models.CharField(max_length=100)  # n#equipo (nombre modificado por compatibilidad)
    foto = models.ImageField(upload_to='reconectadores_fotos/', null=True, blank=True)
    id_nodo = models.ForeignKey('Nodo', on_delete=models.CASCADE)
    serial_reco = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    fecha_instalacion = models.DateField(null=True, blank=True)
    responsable = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    estado_bateria = models.CharField(max_length=100, null=True, blank=True)
    serial_bateria = models.CharField(max_length=100, null=True, blank=True)
    estado_reconectador = models.CharField(max_length=100, null=True, blank=True)
    Icc = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Reco {self.serial_reco}"


class Comunicacion(models.Model):
    id_comunicacion = models.AutoField(primary_key=True)
    modem = models.CharField(max_length=100)
    ip = models.GenericIPAddressField(protocol='both')
    ip_vieja = models.GenericIPAddressField(protocol='both', null=True, blank=True)
    asdu = models.CharField(max_length=100)
    id_reco = models.ForeignKey('Reconectador', on_delete=models.CASCADE)
    estado = models.CharField(max_length=100)
    tecnologia = models.CharField(max_length=100)
    estado_actividad = models.CharField(max_length=100, null=True, blank=True)
    serial_modem = models.CharField(max_length=100)
    activo_modem = models.IntegerField( null=True)

    def __str__(self):
        return f"Comunicacion {self.id_comunicacion} - {self.modem}"        


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)  # este será el nuevo ID
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Trabajador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre_completo = models.CharField(max_length=200)
    cc = models.CharField(max_length=20, unique=True)
    id_rol = models.ForeignKey(Rol, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre_completo
    
class Orden(models.Model):
    TIPO_CHOICES = [
        ('subestacion', 'Subestación'),
        ('reco', 'Reconectador'),
    ]

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pendiente_por_revisar', 'Pendiente por revisar'),
        ('completada', 'Completada'),
    ]

    n_orden = models.CharField(max_length=50)
    descripcion = models.TextField()
    fecha = models.DateField()
    id_nodo = models.ForeignKey(Nodo, on_delete=models.SET_NULL, null=True, blank=True)
    id_subestacion = models.ForeignKey(Subestacion, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    creada_por = models.ForeignKey(Trabajador, on_delete=models.SET_NULL, null=True, related_name='ordenes_creadas')
    asignada_a = models.ForeignKey(Trabajador, on_delete=models.SET_NULL, null=True, related_name='ordenes_asignadas')
    estado_orden = models.CharField(max_length=30, choices=ESTADO_CHOICES)

    def __str__(self):
        return f"Orden {self.n_orden} - {self.tipo}"      
    


class InformeReco(models.Model):
    orden = models.OneToOneField('Orden', on_delete=models.CASCADE, related_name="informe_reco")  
    inicio_actividad = models.DateTimeField()
    falla_identificada = models.TextField()
    causa_falla = models.TextField()
    trabajo_realizado = models.TextField()
    hora_cierre = models.DateTimeField(null=True, blank=True)
    id_fotos = models.CharField(max_length=255, blank=True, null=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7)
    latitud = models.DecimalField(max_digits=10, decimal_places=7)
    
    aviso_telco = models.BooleanField(default=False)  # Marcar con una X si se avisó
    aviso_mante = models.BooleanField(default=False)  # Marcar con una X si se avisó

    detalle_telco = models.TextField(blank=True, null=True)
    detalle_mante = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Informe Reco #{self.id} - Orden #{self.orden.id}" 


class FotoInformeReco(models.Model):
    informe = models.ForeignKey(
        'InformeReco', 
        on_delete=models.CASCADE, 
        related_name="fotos"
    )
    imagen = models.ImageField(upload_to='informes_reco/fotos/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto {self.id} del Informe #{self.informe.id}"
    
class ComentarioIngeniero(models.Model):
    id_comentario = models.AutoField(primary_key=True)
    id_comunicacion = models.ForeignKey(
        'Comunicacion',
        on_delete=models.SET_NULL,  # 👈 Cambiar aquí
        null=True, blank=True
    )
    texto = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario {self.id_comentario} sobre Comunicación {self.id_comunicacion_id}"

class HistoricoReco(models.Model):
    id_histo = models.AutoField(primary_key=True)
    informes = models.ManyToManyField(InformeReco, related_name="historicos")
    id_comentario = models.ForeignKey(
        ComentarioIngeniero,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Histórico {self.id_histo} con {self.informes.count()} informe(s)"       
    

class Historicosubcomu(models.Model):
    id_historico_sub_comu = models.AutoField(primary_key=True)
    informe_sub_comu = models.ForeignKey(Subestacion_comu_informe, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Histórico SubComu {self.id_historico_sub_comu} - Informe {self.informe_sub_comu_id}"


class formu_sube_circuito(models.Model):
    id_formu_sube_circuito = models.AutoField(primary_key=True)

from django.db import models

class OrdenSubestacion(models.Model):
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("pendiente_por_revisar", "pendiente por revisar"),
        ("completada", "Completada"),
    ]

    id_orden = models.AutoField(primary_key=True)
    numero_orden_sube = models.CharField(max_length=50, unique=True)  # Número de orden
    descripcion_orden_sube = models.TextField()  # Detalle de la orden
    estado_orden = models.CharField(max_length=30, choices=ESTADO_CHOICES, default="pendiente")
    fecha = models.DateField(auto_now_add=True)  # Fecha de creación
    id_subestacion = models.ForeignKey("Subestacion", on_delete=models.CASCADE, related_name="ordenes_subestacion")

    def __str__(self):
        return f"OrdenSubestación {self.numero_orden_sube} - {self.get_estado_orden_display()}"

class HistoricoSubestacion(models.Model):
    subestacion = models.ForeignKey("Subestacion", on_delete=models.CASCADE, related_name="historicos")
    orden = models.ForeignKey("OrdenSubestacion", on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    observaciones_generales = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Histórico {self.id} - {self.subestacion.nombre} ({self.fecha.strftime('%d/%m/%Y')})"

class CodigoRecuperacion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.codigo}"