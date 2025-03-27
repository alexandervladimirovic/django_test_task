from decimal import Decimal
from typing import NoReturn

from django.db.models import F, Sum, DecimalField
from django.db.models.functions import Coalesce, Cast

from .models import Section, Building, Expenditure


def get_parent_sections(building_id: int) -> list[Section]:
    """Функция, которая для каждого объекта строительства возвращает список родительских секций `(parent=None)`. У каждой родительской секции дополнительно подсчитан бюджет.

    :param building_id (int): ID здания, для которого нужно получить родительские секции.
    :return: Список родительских секций с бюджетом.

    """

    parent_sections = Section.objects.filter(
        building_id=building_id,
        parent__isnull=True,
    ).annotate(
        budget=Coalesce(
            Sum(F("expenditure__count") * F("expenditure__price")),
            Cast(0, output_field=DecimalField()),
        )
    )

    return list(parent_sections)


def get_buildings() -> list[dict[str, Decimal | int]]:
    """Функция, которая возращает список объектов строительства, у каждого объекта строительства дополнительно посчитана стоимость работ и материалов."""

    obj_buildings = Building.objects.all().values("id")

    expenditures = Expenditure.objects.values("section__building_id", "type").annotate(
        total_amount=Coalesce(
            (Sum(F("count") * F("price"))), Cast(0, output_field=DecimalField())
        )
    )

    # { building_id: { amount_works: Decimal, amount_material: Decimal } }
    expenditures_map = {}

    for expenditure in expenditures:
        building_id = expenditure["section__building_id"]

        if building_id not in expenditures_map:
            expenditures_map[building_id] = {
                "amount_works": Decimal(0),
                "amount_material": Decimal(0),
            }
        if expenditure["type"] == Expenditure.TypesExpenditure.WORK:
            expenditures_map[building_id]["amount_works"] = expenditure["total_amount"]
        else:
            expenditures_map[building_id]["amount_material"] = expenditure[
                "total_amount"
            ]

    result = []

    for building in obj_buildings:
        result.append(
            {
                "id": building["id"],
                "amount_works": expenditures_map.get(building["id"], {}).get(
                    "amount_works", Decimal(0)
                ),
                "amount_material": expenditures_map.get(building["id"], {}).get(
                    "amount_material", Decimal(0)
                ),
            }
        )

    return result


def update_with_discount(section_id: int, discount: Decimal) -> NoReturn:
    """Функция, которая обновляет поле `price` у всех расценок внутри секции с учётом скидки.

    :param discount (Decimal): Размер скидки в % от `Decimal(0) до Decimal(100)`.
    """

    if not (Decimal(0) <= discount <= Decimal(100)):
        raise ValueError("Скидка должна быть в диапазоне от 0 до 100 (в процентах)")

    discount_factor = Decimal(1) - (discount / Decimal(100))

    Expenditure.objects.filter(section_id=section_id).update(
        price=F("price") * discount_factor
    )
