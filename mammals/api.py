import json
import logging
from collections import Counter
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django_ratelimit.decorators import ratelimit

from .models import Mammal
from .views import get_country_from_distribution, get_continent_from_region

logger = logging.getLogger(__name__)

@require_GET
@ratelimit(key='ip', rate='30/m', block=True)
def search(request):
    """Endpoint de busca/filtragem (AJAX) - CORRIGIDO"""
    query = request.GET.get("q", "").strip()
    region_filter = request.GET.get("region", "").strip()
    taxonomy_filter = request.GET.get("taxonomy", "").strip()

    mammals = Mammal.objects.search_api(query, region_filter, taxonomy_filter)

    # Preparar resultados com tratamento de erros
    results = []
    for mammal in mammals:
        try:
            # Usar short_description se existir, senão description truncada
            description = getattr(mammal, "short_description", None)
            if not description:
                description = mammal.description[:200] if mammal.description else ""

            results.append(
                {
                    "id": mammal.id,
                    "common_name": mammal.common_name or "",
                    "binomial_name": mammal.binomial_name or "",
                    "description": description,
                    "image_filename": mammal.image_filename or "",
                    "image_url": (
                        mammal.image.url
                        if mammal.image
                        else (
                            f"/static/images/{mammal.image_filename}"
                            if mammal.image_filename
                            else ""
                        )
                    ),
                    "continent": mammal.continent or "",
                    "taxonomy_order": mammal.taxonomy_order or "",
                }
            )
        except Exception as e:
            # Log erro mas continua processando
            import logging

            logger = logging.getLogger(__name__)
            logger.error("Erro ao processar mammal %s: %s", mammal.id, e)
            continue

    return JsonResponse(results, safe=False)


@require_GET
def global_map_data(request):
    """Endpoint JSON com dados de todas as espécies para o mapa global"""
    try:
        # Buscar todos os mamíferos do banco de dados - incluindo latitude,
        # longitude e distribuição
        mammals = Mammal.objects.only(
            "id",
            "common_name",
            "binomial_name",
            "continent",
            "image_filename",
            "latitude",
            "longitude",
            "distribution",
        ).all()

        # Estrutura para armazenar dados agregados por localização
        location_data = {}
        # Processar cada mamifero uma unica vez
        for mammal in mammals:
            lat = mammal.latitude
            lon = mammal.longitude

            if lat is None or lon is None:
                # Fallback coordinates based on region
                reg = (mammal.region or "").lower()
                if "caribe" in reg:
                    lat, lon = 19.0, -73.0
                elif "australia" in reg:
                    lat, lon = -25.2, 133.7
                elif "asia" in reg:
                    lat, lon = 34.0, 100.0
                elif "americas" in reg:
                    lat, lon = 10.0, -75.0
                elif "madagascar" in reg:
                    lat, lon = -18.7, 46.8
                elif "africa" in reg:
                    lat, lon = 8.7, 20.9
                elif "oceano" in reg:
                    lat, lon = -10.0, 160.0
                elif "europa" in reg:
                    lat, lon = 50.0, 10.0
                else:
                    lat, lon = 0.0, 0.0

            country = get_country_from_distribution(mammal.distribution)
            location_key = f"{lat}_{lon}"
            location_name = country

            if location_key not in location_data:
                location_data[location_key] = {
                    "lat": lat,
                    "lon": lon,
                    "location_name": location_name,
                    "species": [],
                    "count": 0,
                }

            species_info = {
                "id": mammal.pk,
                "common_name": mammal.common_name,
                "binomial_name": mammal.binomial_name,
                "continent": mammal.continent or "Unknown",
                "image_filename": mammal.image_filename or "",
            }

            if not any(
                s["id"] == mammal.pk for s in location_data[location_key]["species"]
            ):
                location_data[location_key]["species"].append(species_info)
                location_data[location_key]["count"] += 1

        locations = list(location_data.values())

        # Calcular estatísticas por continente para o heatmap de territórios
        continent_qs = Mammal.objects.only(
            "id", "common_name", "binomial_name", "region", "image_filename"
        ).all()
        continent_map = {}

        for m in continent_qs:
            reg = (m.region or "").strip()
            if not reg:
                continue

            matched_cont = get_continent_from_region(reg)

            if matched_cont not in continent_map:
                continent_map[matched_cont] = {
                    "continent": matched_cont,
                    "count": 0,
                    "species": [],
                }
            continent_map[matched_cont]["count"] += 1
            continent_map[matched_cont]["species"].append(
                {
                    "id": m.pk,
                    "common_name": m.common_name,
                    "binomial_name": m.binomial_name,
                    "image_filename": m.image_filename or "",
                }
            )
        continent_stats = list(continent_map.values())

        # Compute stats
        total_locations = len(locations)
        sum(loc["count"] for loc in locations)

        # Max concentration grouped by country/region name
        country_counts = {}
        for loc in locations:
            lname = loc.get("location_name", "Unknown")
            if lname not in country_counts:
                country_counts[lname] = 0
            country_counts[lname] += loc["count"]
        max_concentration = max(country_counts.values(), default=0)
        total_species_all = sum(c["count"] for c in continent_stats)

        response_data = {
            "success": True,
            "locations": locations,
            "continent_stats": continent_stats,
            "total_species": total_species_all,
            "statistics": {
                "total_locations": total_locations,
                "total_species": total_species_all,
                "max_concentration": max_concentration,
            },
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_GET
def dashboard_api(request):
    mammals = Mammal.objects.all()

    country_counts = Counter()
    biological_year_counts = Counter()
    formalization_year_counts = Counter()
    continent_counts = Counter()
    taxonomy_counts = Counter()
    region_counts = Counter()
    cause_counts = Counter()

    total = mammals.count()

    for m in mammals:
        if m.distribution:
            country = get_country_from_distribution(m.distribution)
            country_counts[country] += 1

        # 2. Ano de Extinção Biológica (agrupado por década)
        if m.extinction_year:
            decade = (m.extinction_year // 10) * 10
            decade_str = f"{decade}s"
            biological_year_counts[decade_str] += 1

        # 3. Ano de Formalização (agrupado por década)
        if m.formalization_year:
            decade = (m.formalization_year // 10) * 10
            decade_str = f"{decade}s"
            formalization_year_counts[decade_str] += 1

        if m.region:
            continent_counts[get_continent_from_region(m.region)] += 1
        # 5. Taxonomy
        if m.taxonomy_order:
            taxonomy_counts[m.taxonomy_order] += 1

        # 6. Region (novo campo)
        if m.region:
            region_counts[m.region] += 1

        # 7. Main cause (agrupada)
        if m.main_cause:
            cause_raw = m.main_cause.lower()
            if "caca" in cause_raw or "caça" in cause_raw:
                cause_counts["Caça"] += 1
            if "invasor" in cause_raw:
                cause_counts["Espécies Invasoras"] += 1
            if "habitat" in cause_raw or "desmatamento" in cause_raw:
                cause_counts["Perda de Habitat"] += 1
            if "coloniz" in cause_raw:
                cause_counts["Colonização"] += 1
            if "clima" in cause_raw:
                cause_counts["Mudança Climática"] += 1

    return JsonResponse(
        {
            "total": total,
            "countries": dict(country_counts),
            "biological_years": dict(biological_year_counts),
            "formalization_years": dict(formalization_year_counts),
            "eras": dict(biological_year_counts),  # backward compat
            "continents": dict(continent_counts),
            "taxonomy": dict(taxonomy_counts),
            "regions": dict(region_counts),
            "causes": dict(cause_counts),
        }
    )


@require_POST
@csrf_exempt
def log_js_error(request):
    try:
        # Estrutura para armazenar dados agregados por localização
        location_data = {}
        # Processar cada mamifero uma unica vez
        for mammal in mammals:
            lat = mammal.latitude
            lon = mammal.longitude

            if lat is None or lon is None:
                # Fallback coordinates based on region
                reg = (mammal.region or "").lower()
                if "caribe" in reg:
                    lat, lon = 19.0, -73.0
                elif "australia" in reg:
                    lat, lon = -25.2, 133.7
                elif "asia" in reg:
                    lat, lon = 34.0, 100.0
                elif "americas" in reg:
                    lat, lon = 10.0, -75.0
                elif "madagascar" in reg:
                    lat, lon = -18.7, 46.8
                elif "africa" in reg:
                    lat, lon = 8.7, 20.9
                elif "oceano" in reg:
                    lat, lon = -10.0, 160.0
                elif "europa" in reg:
                    lat, lon = 50.0, 10.0
                else:
                    lat, lon = 0.0, 0.0

            country = get_country_from_distribution(mammal.distribution)
            location_key = f"{lat}_{lon}"
            location_name = country

            if location_key not in location_data:
                location_data[location_key] = {
                    "lat": lat,
                    "lon": lon,
                    "location_name": location_name,
                    "species": [],
                    "count": 0,
                }

            species_info = {
                "id": mammal.pk,
                "common_name": mammal.common_name,
                "binomial_name": mammal.binomial_name,
                "continent": mammal.continent or "Unknown",
                "image_filename": mammal.image_filename or "",
            }

            if not any(
                s["id"] == mammal.pk for s in location_data[location_key]["species"]
            ):
                location_data[location_key]["species"].append(species_info)
                location_data[location_key]["count"] += 1

        locations = list(location_data.values())

        # Calcular estatísticas por continente para o heatmap de territórios
        continent_qs = Mammal.objects.only(
            "id", "common_name", "binomial_name", "region", "image_filename"
        ).all()
        continent_map = {}

        for m in continent_qs:
            reg = (m.region or "").strip()
            if not reg:
                continue

            matched_cont = get_continent_from_region(reg)

            if matched_cont not in continent_map:
                continent_map[matched_cont] = {
                    "continent": matched_cont,
                    "count": 0,
                    "species": [],
                }
            continent_map[matched_cont]["count"] += 1
            continent_map[matched_cont]["species"].append(
                {
                    "id": m.pk,
                    "common_name": m.common_name,
                    "binomial_name": m.binomial_name,
                    "image_filename": m.image_filename or "",
                }
            )
        continent_stats = list(continent_map.values())

        # Compute stats
        total_locations = len(locations)
        sum(loc["count"] for loc in locations)

        # Max concentration grouped by country/region name
        country_counts = {}
        for loc in locations:
            lname = loc.get("location_name", "Unknown")
            if lname not in country_counts:
                country_counts[lname] = 0
            country_counts[lname] += loc["count"]
        max_concentration = max(country_counts.values(), default=0)
        total_species_all = sum(c["count"] for c in continent_stats)

        response_data = {
            "success": True,
            "locations": locations,
            "continent_stats": continent_stats,
            "total_species": total_species_all,
            "statistics": {
                "total_locations": total_locations,
                "total_species": total_species_all,
                "max_concentration": max_concentration,
            },
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_GET
def dashboard_api(request):
    mammals = Mammal.objects.all()

    country_counts = Counter()
    biological_year_counts = Counter()
    formalization_year_counts = Counter()
    continent_counts = Counter()
    taxonomy_counts = Counter()
    region_counts = Counter()
    cause_counts = Counter()

    total = mammals.count()

    for m in mammals:
        if m.distribution:
            country = get_country_from_distribution(m.distribution)
            country_counts[country] += 1

        # 2. Ano de Extinção Biológica (agrupado por década)
        if m.extinction_year:
            decade = (m.extinction_year // 10) * 10
            decade_str = f"{decade}s"
            biological_year_counts[decade_str] += 1

        # 3. Ano de Formalização (agrupado por década)
        if m.formalization_year:
            decade = (m.formalization_year // 10) * 10
            decade_str = f"{decade}s"
            formalization_year_counts[decade_str] += 1

        if m.region:
            continent_counts[get_continent_from_region(m.region)] += 1
        # 5. Taxonomy
        if m.taxonomy_order:
            taxonomy_counts[m.taxonomy_order] += 1

        # 6. Region (novo campo)
        if m.region:
            region_counts[m.region] += 1

        # 7. Main cause (agrupada)
        if m.main_cause:
            cause_raw = m.main_cause.lower()
            if "caca" in cause_raw or "caça" in cause_raw:
                cause_counts["Caça"] += 1
            if "invasor" in cause_raw:
                cause_counts["Espécies Invasoras"] += 1
            if "habitat" in cause_raw or "desmatamento" in cause_raw:
                cause_counts["Perda de Habitat"] += 1
            if "coloniz" in cause_raw:
                cause_counts["Colonização"] += 1
            if "clima" in cause_raw:
                cause_counts["Mudança Climática"] += 1

    return JsonResponse(
        {
            "total": total,
            "countries": dict(country_counts),
            "biological_years": dict(biological_year_counts),
            "formalization_years": dict(formalization_year_counts),
            "eras": dict(biological_year_counts),  # backward compat
            "continents": dict(continent_counts),
            "taxonomy": dict(taxonomy_counts),
            "regions": dict(region_counts),
            "causes": dict(cause_counts),
        }
    )


logger = logging.getLogger("django.security")

@require_POST
@csrf_exempt
@ratelimit(key="ip", rate="10/m", block=True)
def log_js_error(request):
    try:
        data = json.loads(request.body)
        logger.warning(f"JS Error: {json.dumps(data)}")
    except json.JSONDecodeError:
        pass
    except Exception:
        pass
    return HttpResponse("OK")


from django.db import connection

@require_GET
def health_check(request):
    try:
        connection.ensure_connection()
        return JsonResponse({'status': 'ok', 'db': 'connected'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'db': str(e)}, status=503)
