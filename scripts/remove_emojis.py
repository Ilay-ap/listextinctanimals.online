import os
import re

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "extinct_mammals_django.settings")
django.setup()

from mammals.models import Mammal

auroque = Mammal.objects.filter(common_name__icontains="auroque").first()
emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]|[\u2600-\u27BF]", flags=re.UNICODE)

if auroque:
    for field in [
        "description",
        "habitat",
        "extinction_causes",
        "distribution",
        "ecological_impact",
        "conservation_legacy",
        "fun_facts",
        "taxonomy_extended",
    ]:
        val = getattr(auroque, field)
        if val:
            val = emoji_pattern.sub("", val)
            setattr(auroque, field, val)

    auroque.save()
    print("Auroch emojis completely removed.")
else:
    print("Auroch not found.")
