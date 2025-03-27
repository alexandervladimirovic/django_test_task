from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Building(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("наименование объекта"))

    class Meta:
        verbose_name = _("объект строительства")


class Section(models.Model):
    building = models.ForeignKey(
        Building, on_delete=models.PROTECT, verbose_name=_("объект")
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        verbose_name=_("родительская секция"),
        blank=False,
        null=True,
    )

    class Meta:
        verbose_name = _("секция сметы")

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.id and self.parent and getattr(self.parent, "parent", None):
            raise ValidationError("Максимальный уровень вложенности 2")
        super().save(force_insert, force_update, using, update_fields)


class Expenditure(models.Model):
    class TypesExpenditure(models.TextChoices):
        WORK = "Работа"
        MATERIAL = "Материал"

    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        help_text=_(
            "расценка может принадлежать только той секции, у которой указан parent"
        ),
    )
    name = models.CharField(max_length=255, verbose_name=_("название расценки"))
    type = models.CharField(
        verbose_name=_("тип расценки"), choices=TypesExpenditure.choices, max_length=8
    )
    count = models.DecimalField(
        verbose_name=_("количество материала"), max_digits=20, decimal_places=8
    )
    price = models.DecimalField(
        verbose_name=_("цена за единицу товара"), max_digits=20, decimal_places=2
    )

    class Meta:
        verbose_name = _("расценка сметы")
