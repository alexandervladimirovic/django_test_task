from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ConstructServiceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "construct_service"

    verbose_name = _("Сервис для строительства")
