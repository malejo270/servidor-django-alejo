from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Subestacion,Nodo,Orden,Subestacion_comu_informe,InformeReco,FotoInformeReco,Pregunta,PreguntaPadre,OrdenSubestacion,Trabajador, Rol
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Correo",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Correo emcali'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )

class SubestacionForm(forms.ModelForm):
    class Meta:
        model = Subestacion  
        fields = ['nombre', 'ubicacion']
class NodoForm(forms.ModelForm):
    id_subestacion = forms.ModelChoiceField(
        queryset=Subestacion.objects.all(),
        label="Subestación",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Nodo
        fields = ['nodo', 'direccion', 'longitud', 'latitud', 
                  'circuito1', 'circuito2', 'clasificacion', 'nt', 'id_subestacion']

class OrdenForm(forms.ModelForm):
    # Campos extra para buscar nodo/subestación por nombre
    nombre_nodo_reco = forms.CharField(required=False, label="Nodo (si es Reco)")
    nombre_subestacion_texto = forms.CharField(required=False, label="Subestación (si aplica)")

    class Meta:
        model = Orden
        fields = ['n_orden', 'descripcion', 'fecha', 'tipo', 'creada_por', 'asignada_a']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }                  

class SubestacionComuInformeForm(forms.ModelForm):
    class Meta:
        model = Subestacion_comu_informe
        fields = [
           
            'trabajo_realizado_sub_comu',
            'otras_observaciones',
            'latitud_sub',
            'longitud_sub',
        ] 
        widgets = {
            'latitud_sub': forms.HiddenInput(),
            'longitud_sub': forms.HiddenInput(),
        }

class InformeRecoForm(forms.ModelForm):
    class Meta:
        model = InformeReco
        fields = [
            'falla_identificada',
            'causa_falla',
            'trabajo_realizado',
            'longitud',
            'latitud',
            'aviso_telco',
            'aviso_mante',
            'detalle_telco',
            'detalle_mante',
        ]


class TresFotosForm(forms.Form):
    foto1 = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'accept': 'image/*',
            'capture': 'environment'
        }),
        required=False,
        label="Foto 1"
    )
    foto2 = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'accept': 'image/*',
            'capture': 'environment'
        }),
        required=False,
        label="Foto 2"
    )
    foto3 = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'accept': 'image/*',
            'capture': 'environment'
        }),
        required=False,
        label="Foto 3"
    )

class PreguntaForm(forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = ["texto", "tipo", "categoria", "padre"]
        widgets = {
            'texto': forms.Textarea(attrs={
                'rows': 3, 
                'style': 'width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;',
                'placeholder': 'Ingrese el texto de la pregunta...'
            }),
            'tipo': forms.Select(attrs={
                'style': 'width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;'
            }),
            'categoria': forms.Select(attrs={
                'style': 'width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;',
                'id': 'id_categoria'
            }),
            'padre': forms.Select(attrs={
                'style': 'width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;',
                'id': 'id_padre'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Inicialmente mostrar preguntas padre vacías
        self.fields["padre"].queryset = PreguntaPadre.objects.none()

        # Si estamos editando una instancia existente, cargar los padres de esa categoría
        if self.instance.pk and self.instance.categoria:
            self.fields["padre"].queryset = PreguntaPadre.objects.filter(categoria=self.instance.categoria)


class OrdenSubestacionForm(forms.ModelForm):
    class Meta:
        model = OrdenSubestacion
        fields = ["numero_orden_sube", "descripcion_orden_sube", "id_subestacion"]  # 👈 quitamos estado_orden

        widgets = {
            "numero_orden_sube": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Número de orden"
            }),
            "descripcion_orden_sube": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Descripción de la orden"
            }),
            "id_subestacion": forms.Select(attrs={
                "class": "form-control"
            }),
        }

        labels = {
            "numero_orden_sube": "Número de Orden",
            "descripcion_orden_sube": "Descripción",
            "id_subestacion": "Subestación",
        }
class PreguntaPadreForm(forms.ModelForm):
    class Meta:
        model = PreguntaPadre
        fields = ["texto", "categoria"]

class InformeRecoForm(forms.ModelForm):
    class Meta:
        model = InformeReco
        fields = [
            'falla_identificada', 
            'causa_falla', 
            'trabajo_realizado', 
            'latitud', 
            'longitud',
            'aviso_telco', 
            'detalle_telco', 
            'aviso_mante', 
            'detalle_mante'
        ]
        widgets = {
            'falla_identificada': forms.Select(attrs={
                'class': 'form-control',
                'required': 'required'
            }),
            'causa_falla': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'required': 'required',
                'placeholder': 'Describe la causa de la falla...'
            }),
            'trabajo_realizado': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'required': 'required',
                'placeholder': 'Describe el trabajo realizado...'
            }),
            'detalle_telco': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Detalle del aviso a TELCO...'
            }),
            'detalle_mante': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Detalle del aviso a Mantenimiento...'
            }),
        }


class UsuarioRegistroForm(forms.Form):
    username = forms.CharField(label="Correo emcali", max_length=150)
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    nombre_completo = forms.CharField(label="Nombre completo", max_length=200)
    cc = forms.CharField(label="Cédula", max_length=20)
    rol = forms.ModelChoiceField(queryset=Rol.objects.all(), label="Rol")        