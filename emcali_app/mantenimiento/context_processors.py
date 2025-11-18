from .models import Trabajador

def user_role_context(request):
    """
    Agrega el rol del usuario autenticado al contexto global.
    """
    user_role = None

    if request.user.is_authenticated:
        try:
            trabajador = Trabajador.objects.select_related('id_rol').get(user=request.user)
            user_role = trabajador.id_rol.nombre.lower()  # Ejemplo: 'ingeniero' o 'operario'
        except Trabajador.DoesNotExist:
            user_role = None

    return {'user_role': user_role}
