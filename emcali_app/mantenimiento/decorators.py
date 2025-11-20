from django.shortcuts import redirect,render
from django.contrib import messages

def role_required(*roles):
    """
    Decorador que permite acceso solo a usuarios cuyo rol esté en la lista.
    Ejemplo: @role_required('jefe', 'operario')
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            try:
                rol_usuario = request.user.trabajador.id_rol.nombre.lower()
            except:
                messages.error(request, "El usuario no tiene un rol asignado.")
                return redirect('login')

            if rol_usuario not in roles:
                messages.error(request, "No tienes permiso para acceder a esta página.")
                return render(request, 'error_acceso.html', status=404)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
