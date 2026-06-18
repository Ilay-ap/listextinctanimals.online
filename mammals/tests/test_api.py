import pytest
from django.urls import reverse
from mammals.models import Mammal

@pytest.mark.django_db
def test_dashboard_api(client):
    Mammal.objects.create(
        common_name="Test Mammal",
        binomial_name="Testus mammalicus",
        distribution="Brazil",
        extinction_year=2000,
        region="América do Sul",
        taxonomy_order="Carnivora",
        main_cause="Caça"
    )
    url = reverse("mammals:dashboard_api")
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["countries"]["Brazil"] == 1
    assert data["biological_years"]["2000s"] == 1
    assert data["continents"]["América do Sul"] == 1
    assert data["taxonomy"]["Carnivora"] == 1
    assert data["causes"]["Caça"] == 1
