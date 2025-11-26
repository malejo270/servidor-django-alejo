from django.shortcuts import redirect, render
from django.contrib import messages

def role_required(*roles):
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
                return render(request, 'login.html', status=403)
                # O si quieres mandarlo al login:
                # return redirect('login')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
