from decimal import Decimal
from django.test import TestCase
from .models import Building, Section, Expenditure
from .services import get_parent_sections, get_buildings, update_with_discount


class GetParentSectionsTestCase(TestCase):
    def setUp(self):
        # Объекты
        self.building_1 = Building.objects.create(name="Объект 1")
        self.building_2 = Building.objects.create(name="Объект 2")
        self.building_3 = Building.objects.create(name="Объект 3")

        # Родительские секции
        self.parent_section_1 = Section.objects.create(
            building=self.building_1, parent=None
        )
        self.parent_section_2 = Section.objects.create(
            building=self.building_2, parent=None
        )
        self.parent_section_3 = Section.objects.create(
            building=self.building_3, parent=None
        )
        self.parent_section_4 = Section.objects.create(
            building=self.building_2, parent=None
        )

        # Расходы
        Expenditure.objects.create(
            section=self.parent_section_1,
            name="Работа 1",
            type=Expenditure.TypesExpenditure.WORK,
            count=5.0,
            price=5.0,
        )
        Expenditure.objects.create(
            section=self.parent_section_1,
            name="Работа 2",
            type=Expenditure.TypesExpenditure.WORK,
            count=20.0,
            price=10.0,
        )

        Expenditure.objects.create(
            section=self.parent_section_2,
            name="Материал 1",
            type=Expenditure.TypesExpenditure.MATERIAL,
            count=5.0,
            price=15.0,
        )

        Expenditure.objects.create(
            section=self.parent_section_3,
            name="Материал 2",
            type=Expenditure.TypesExpenditure.MATERIAL,
            count=30.0,
            price=8.0,
        )

    def test_type_get_parent_sections(self):
        result = get_parent_sections(building_id=self.building_1.id)

        self.assertEqual(type(result), list)

    def test_result_get_parent_sections(self):
        result = get_parent_sections(building_id=self.building_2.id)

        expected_budget = Decimal("75")

        self.assertEqual(result[0].building, self.building_2)
        self.assertEqual(result[0].building_id, self.building_2.id)
        self.assertEqual(result[0].parent, None)
        self.assertEqual(result[0].budget, expected_budget)

    def test_get_parent_sections_with_no_budget(self):
        result = get_parent_sections(building_id=self.building_2.id)
        self.assertEqual(result[0].budget, Decimal(75))
        self.assertEqual(result[1].budget, Decimal(0))

    def test_get_parent_sections_multiple_buildings(self):
        result_1 = get_parent_sections(building_id=self.building_2.id)
        result_2 = get_parent_sections(building_id=self.building_3.id)

        self.assertEqual(len(result_1), 2)

        self.assertEqual(len(result_2), 1)
        self.assertEqual(result_2[0].budget, Decimal(240))


class GetBuildingTestCase(TestCase):
    def setUp(self):
        # Объекты
        self.building_1 = Building.objects.create(name="Объект 1")
        self.building_2 = Building.objects.create(name="Объект 2")

        # Секции
        self.section_1 = Section.objects.create(building=self.building_1, parent=None)
        self.section_2 = Section.objects.create(
            building=self.building_2, parent=self.section_1
        )

        Expenditure.objects.create(
            section=self.section_1,
            name="Работа 1",
            type=Expenditure.TypesExpenditure.WORK,
            count=10.0,
            price=100.0,
        )
        Expenditure.objects.create(
            section=self.section_1,
            name="Работа 2",
            type=Expenditure.TypesExpenditure.WORK,
            count=5.0,
            price=50.0,
        )
        Expenditure.objects.create(
            section=self.section_2,
            name="Материал 1",
            type=Expenditure.TypesExpenditure.MATERIAL,
            count=7.0,
            price=10.0,
        )
        Expenditure.objects.create(
            section=self.section_2,
            name="Материал 2",
            type=Expenditure.TypesExpenditure.MATERIAL,
            count=3.0,
            price=7.0,
        )

    def test_type_get_building(self):
        result = get_buildings()

        self.assertEqual(type(result), list)

    def test_get_building(self):
        result = get_buildings()
        self.assertEqual(len(result), 2)

        building_dt = {b["id"]: b for b in result}

        self.assertEqual(
            building_dt[self.building_1.id]["amount_works"], Decimal(1250.0)
        )
        self.assertEqual(building_dt[self.building_1.id]["amount_material"], Decimal(0))
        self.assertEqual(building_dt[self.building_2.id]["amount_works"], Decimal(0))
        self.assertEqual(
            building_dt[self.building_2.id]["amount_material"], Decimal(91)
        )

    def test_get_building_no_result(self):
        Building.objects.create()
        result = get_buildings()

        self.assertEqual(len(result), 3)
        self.assertEqual(result[-1]["amount_works"], Decimal(0))
        self.assertEqual(result[-1]["amount_material"], Decimal(0))


class UpdateWithDiscount(TestCase):
    def setUp(self):
        self.building_1 = Building.objects.create(name="Объект 1")

        self.section_1 = Section.objects.create(building=self.building_1, parent=None)
        self.section_2 = Section.objects.create(building=self.building_1, parent=None)

        self.expenditure_1 = Expenditure.objects.create(
            section=self.section_1,
            name="Работа 1",
            type=Expenditure.TypesExpenditure.WORK,
            count=1.0,
            price=100.0,
        )
        self.expenditure_2 = Expenditure.objects.create(
            section=self.section_1,
            name="Работа 2",
            type=Expenditure.TypesExpenditure.MATERIAL,
            count=2.0,
            price=50.0,
        )
    
    def test_update_with_discount(self):
        update_with_discount(section_id=self.section_1.id, discount=Decimal(50))

        self.expenditure_1.refresh_from_db()
        self.expenditure_2.refresh_from_db()

        self.assertEqual(self.expenditure_1.price, Decimal(50))
        self.assertEqual(self.expenditure_2.price, Decimal(25))
    
    def test_update_with_discount_invalid_discount(self):
        with self.assertRaises(ValueError):
            update_with_discount(section_id=self.section_1, discount=Decimal(-10))
        
        with self.assertRaises(ValueError):
            update_with_discount(section_id=self.section_2, discount=Decimal(110))
    
    def test_update_with_discount_zero_discount(self):
        update_with_discount(section_id=self.section_1.id, discount=Decimal(0))

        self.expenditure_1.refresh_from_db()
        self.expenditure_2.refresh_from_db()

        self.assertEqual(self.expenditure_1.price, Decimal(100))
        self.assertEqual(self.expenditure_2.price, Decimal(50))
    
    def test_update_with_full_discount(self):
        update_with_discount(section_id=self.section_1.id, discount=Decimal(100))

        self.expenditure_1.refresh_from_db()
        self.expenditure_2.refresh_from_db()
        
        self.assertEqual(self.expenditure_1.price, Decimal(0))
        self.assertEqual(self.expenditure_2.price, Decimal(0))