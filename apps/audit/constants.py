from django.utils.translation import gettext_lazy as _


class Action:
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"

    CHOICES = [
        (CREATE, _("Erstellt")),
        (UPDATE, _("Geändert")),
        (DELETE, _("Gelöscht")),
        (LOGIN, _("Angemeldet")),
        (LOGOUT, _("Abgemeldet")),
        (LOGIN_FAILED, _("Anmeldung fehlgeschlagen")),
    ]
