from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


def axes_lockout_response(request, credentials, *args, **kwargs):
    """Handle django-axes lockout with a generic error (no information leakage).

    Returns the login page with the same error message as a wrong password,
    so an attacker cannot distinguish a locked account from wrong credentials.
    """
    from .forms import LoginForm

    form = LoginForm(request=request)
    form.add_error(None, _("Benutzername oder Passwort falsch."))
    return render(request, "accounts/login.html", {"form": form})
