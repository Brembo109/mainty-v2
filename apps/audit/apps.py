from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit"
    label = "audit"

    def ready(self):
        # Import signals module to register @receiver-decorated auth handlers.
        import apps.audit.signals as audit_signals  # noqa: F401

        # Wire model signals for every AuditedModel subclass currently loaded.
        from django.apps import apps

        from .mixins import AuditedModel
        from .signals import connect_audit_signals

        for model in apps.get_models():
            if issubclass(model, AuditedModel):
                connect_audit_signals(model)
