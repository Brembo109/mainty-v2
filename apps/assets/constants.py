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

    # Badge CSS classes per status — matches design system (badge + border, like audit)
    BADGE_CLASS = {
        FREE: "badge-success border border-status-success",
        LOCKED: "badge-warning border border-status-warning",
        OUT_OF_SERVICE: "badge-danger border border-status-danger",
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
