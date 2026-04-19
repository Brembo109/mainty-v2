from django.utils.translation import gettext_lazy as _


class AssetStatus:
    FREE = "free"
    LOCKED = "locked"
    OUT_OF_SERVICE = "out_of_service"

    CHOICES = [
        (FREE, _("Frei")),
        (LOCKED, _("Gesperrt")),
        (OUT_OF_SERVICE, _("Außer Betrieb")),
    ]

    BADGE_CLASS = {
        FREE: "status-dot status-dot-ok",
        LOCKED: "status-dot status-dot-warn",
        OUT_OF_SERVICE: "status-dot status-dot-danger",
    }


class Department:
    HERSTELLUNG = "herstellung"
    QUALITAETSKONTROLLE = "qualitaetskontrolle"
    PROZESSENTWICKLUNG = "prozessentwicklung"

    CHOICES = [
        (HERSTELLUNG, _("Herstellung")),
        (QUALITAETSKONTROLLE, _("Qualitätskontrolle")),
        (PROZESSENTWICKLUNG, _("Prozessentwicklung")),
    ]
