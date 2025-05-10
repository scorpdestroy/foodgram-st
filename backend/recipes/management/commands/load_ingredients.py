import json
import pathlib

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загружает ингредиенты из data/ingredients.json"

    def handle(self, *args, **options):

        DATA_DIR = pathlib.Path(settings.BASE_DIR).parent / "data"
        path = DATA_DIR / "ingredients.json"

        if not path.exists():
            raise CommandError(f"Файл не найден: {path}")

        with path.open(encoding="utf‑8") as f:
            data = json.load(f)

        created, skipped = 0, 0
        for item in data:
            obj, is_created = Ingredient.objects.get_or_create(
                name=item["name"],
                measurement_unit=item["measurement_unit"],
            )
            created += is_created
            skipped += not is_created

        self.stdout.write(
            self.style.SUCCESS(
                f"Добавлено {created}, пропущено {skipped} (уже были)"
            )
        )
