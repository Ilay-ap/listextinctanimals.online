from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def admin_required(view_func):
    """
    Decorator para views que requerem privilégios de administrador.
    Verifica se o usuário está autenticado e se tem is_admin=True no perfil.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Por favor, faça login para acessar esta página.")
            return redirect("accounts:login")

        # Verificar se o usuário é superuser, staff ou se tem is_admin no perfil
        is_admin_profile = (
            hasattr(request.user, "profile") and request.user.profile.is_admin
        )
        if request.user.is_superuser or request.user.is_staff or is_admin_profile:
            return view_func(request, *args, **kwargs)

        messages.error(request, "Acesso negado. Você precisa ser administrador.")
        return redirect("mammals:index")

    return wrapper
