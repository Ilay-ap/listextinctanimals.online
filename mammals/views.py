import json
import unicodedata
from collections import Counter

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import get_language, gettext_lazy as _
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from accounts.models import UserProfile
from .models import Mammal, Comment, Favorite
from .decorators import admin_required
from .translation_service import TranslatedMammal

User = get_user_model()


def get_country_from_distribution(distribution):
    """Retorna o país ou região baseado no campo distribution"""
    dist_clean = normalize_text(distribution)
    country_map = {
        ("australia", "gales do sul", "queensland", "victoria", "tasmania", "macquarie", "ilha christmas", "nova gales"): "Austrália",
        ("cuba",): "Cuba",
        ("hispaniola", "republica dominicana", "haiti"): "Hispaniola",
        ("madagascar",): "Madagascar",
        ("japao", "japan"): "Japão",
        ("mexico",): "México",
        ("brasil",): "Brasil",
        ("indonesia",): "Indonésia",
        ("nova zelandia", "new zealand", "maori"): "Nova Zelândia",
        ("caribe", "porto rico", "jamaica", "barbuda", "antinhas", "antilhas"): "Ilhas do Caribe",
        ("salomao",): "Ilhas Salomão",
        ("argentina",): "Argentina",
        ("peru",): "Peru",
        ("colombia",): "Colômbia",
        ("chile",): "Chile",
        ("falkland", "malvinas"): "Ilhas Malvinas",
        ("galapagos", "equador"): "Equador (Galápagos)",
        ("mauricio", "reuniao", "rodrigues"): "Ilhas Mascarenhas",
        ("argelia", "marrocos", "norte da africa"): "Norte da África",
        ("russia", "siberia"): "Rússia",
        ("canada",): "Canadá",
        ("estados unidos", "eua", "california", "texas"): "Estados Unidos"
    }

    for keys, val in country_map.items():
        if any(k in dist_clean for k in keys):
            return val

    # Fallback
    parts = str(distribution).split(',', maxsplit=1)
    return parts[-1].split('(', maxsplit=1)[0].strip() if len(parts) > 1 else str(distribution).split('(', maxsplit=1)[0].strip()


def get_continent_from_region(region):
    """Mapeia as regiões simplificadas para os continentes"""
    reg = str(region or '').strip()
    if not reg:
        return 'Unknown'

    if "Americas" in reg:
        return 'Américas'
    if "Asia" in reg:
        return 'Ásia'
    if "Europa" in reg:
        return 'Europa'
    if "Oceano" in reg or "Australia" in reg:
        return 'Oceania'
    if "Madagascar" in reg or "Africa" in reg:
        return 'África'
    if "Caribe" in reg:
        return 'Caribe'
    return reg


def index(request):
    """Página inicial com lista de mamíferos"""
    # Otimizar query - carregar apenas campos necessários
    mammals_list = Mammal.objects.only(
        'id', 'common_name', 'binomial_name', 'description',
        'image', 'image_filename', 'continent', 'taxonomy_order'
    ).all()

    # Paginação - 24 mamíferos por página
    paginator = Paginator(mammals_list, 24)
    page = request.GET.get('page', 1)

    try:
        mammals = paginator.page(page)
    except PageNotAnInteger:
        mammals = paginator.page(1)
    except EmptyPage:
        mammals = paginator.page(paginator.num_pages)

    # Traduzir mamíferos para o idioma atual
    current_lang = get_language()
    # Normalizar código de idioma (pt-br -> pt, en-us -> en)
    lang_code = current_lang.split('-')[0] if current_lang else 'pt'
    if lang_code != 'pt':
        mammals.object_list = [
            TranslatedMammal(
                m, current_lang) for m in mammals.object_list]

    # Obter favoritos do usuário se autenticado
    favorites = []
    if request.user.is_authenticated:
        favorites = list(
            request.user.favorites.values_list(
                'mammal_id', flat=True))

    context = {
        'mammals': mammals,
        'favorites': favorites,
        'is_paginated': paginator.num_pages > 1,
    }

    return render(request, 'mammals/index.html', context)


def mammal_detail(request, pk):
    """Página de detalhes de um mamífero"""

    # Otimizar query - carregar comentários com usuários em uma query
    mammal_obj = get_object_or_404(
        Mammal.objects.prefetch_related('comments__user'),
        pk=pk
    )

    # Traduzir mamífero para o idioma atual
    current_lang = get_language()
    # Normalizar código de idioma
    lang_code = current_lang.split('-')[0] if current_lang else 'pt'
    if lang_code != 'pt':
        mammal = TranslatedMammal(mammal_obj, current_lang)
    else:
        mammal = mammal_obj

    comments = mammal.mammal.comments.select_related('user').all() if hasattr(
        mammal, 'mammal') else mammal.comments.select_related('user').all()

    # Verificar se é favorito (sempre usar mammal_obj original)
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(
            user=request.user,
            mammal=mammal_obj
        ).exists()

    # Obter coordenadas diretamente do banco de dados (já auditado)
    map_data = None
    if mammal_obj.latitude is not None and mammal_obj.longitude is not None:
        location_name = "Desconhecido"
        if mammal_obj.distribution:
            location_name = str(mammal_obj.distribution).split(',')[0].strip()

        map_data = {
            'coordinates': [
                {
                    'lat': mammal_obj.latitude,
                    'lon': mammal_obj.longitude,
                    'location': location_name}],
            'center': {
                'lat': mammal_obj.latitude,
                'lon': mammal_obj.longitude},
            'zoom': 5,
        }

    context = {
        'mammal': mammal,
        'comments': comments,
        'is_favorite': is_favorite,
        'map_data': json.dumps(map_data) if map_data else None,
    }

    return render(request, 'mammals/detail.html', context)


def about(request):
    """Página sobre o projeto"""
    return render(request, 'mammals/about.html')


@login_required
def favorites_view(request):
    """Página de favoritos do usuário"""
    favorites = request.user.favorites.select_related('mammal').all()

    # Traduzir mamíferos favoritos
    current_lang = get_language()
    # Normalizar código de idioma
    lang_code = current_lang.split('-')[0] if current_lang else 'pt'

    # Criar lista de mamíferos traduzidos para o template
    mammals_list = []
    for fav in favorites:
        if lang_code != 'pt':
            mammal = TranslatedMammal(fav.mammal, current_lang)
        else:
            mammal = fav.mammal
        mammals_list.append({
            'favorite': fav,
            'mammal': mammal
        })

    context = {
        'favorites': mammals_list,
    }

    return render(request, 'mammals/favorites.html', context)


def search(request):
    """Endpoint de busca/filtragem (AJAX) - CORRIGIDO"""
    query = request.GET.get('q', '').strip()
    region_filter = request.GET.get('region', '').strip()
    taxonomy_filter = request.GET.get('taxonomy', '').strip()

    # Otimizar query - carregar apenas campos necessários
    mammals = Mammal.objects.only(
        'id', 'common_name', 'binomial_name', 'description',
        'image', 'image_filename', 'continent', 'taxonomy_order'
    ).all()  # IMPORTANTE: .all() para retornar todos quando não há filtros

    # Aplicar filtros apenas se existirem
    if query:
        mammals = mammals.filter(
            Q(common_name__icontains=query) |
            Q(binomial_name__icontains=query) |
            Q(description__icontains=query)
        )

    if region_filter and region_filter.lower() != 'all':
        mammals = mammals.filter(continent__iexact=region_filter)

    if taxonomy_filter and taxonomy_filter.upper() != 'ALL':
        mammals = mammals.filter(taxonomy_order__iexact=taxonomy_filter)

    # Preparar resultados com tratamento de erros
    results = []
    for mammal in mammals:
        try:
            # Usar short_description se existir, senão description truncada
            description = getattr(mammal, 'short_description', None)
            if not description:
                description = mammal.description[:
                                                 200] if mammal.description else ''

            results.append(
                {
                    'id': mammal.id,
                    'common_name': mammal.common_name or '',
                    'binomial_name': mammal.binomial_name or '',
                    'description': description,
                    'image_filename': mammal.image_filename or '',
                    'image_url': mammal.image.url if mammal.image else (
                        f'/static/images/{mammal.image_filename}' if mammal.image_filename else ''),
                    'continent': mammal.continent or '',
                    'taxonomy_order': mammal.taxonomy_order or '',
                })
        except Exception as e:
            # Log erro mas continua processando
            print(f"Erro ao processar mammal {mammal.id}: {e}")
            continue

    return JsonResponse(results, safe=False)


# ============================================================================
# ADMIN VIEWS - CRUD de Mamíferos
# ============================================================================

@admin_required
def admin_mammals(request):
    """Página administrativa de mamíferos"""
    mammals = Mammal.objects.all()

    context = {
        'mammals': mammals,
    }

    return render(request, 'admin_panel/mammals.html', context)


@admin_required
def admin_add_mammal(request):
    """Adicionar novo mamífero"""
    if request.method == 'POST':
        common_name = request.POST.get('common_name', '').strip()
        binomial_name = request.POST.get('binomial_name', '').strip()
        description = request.POST.get('description', '').strip()
        habitat = request.POST.get('habitat', '').strip()
        distribution = request.POST.get('distribution', '').strip()
        extinction_causes = request.POST.get('extinction_causes', '').strip()
        image_filename = request.POST.get('image_filename', '').strip()
        continent = request.POST.get('continent', '').strip()
        taxonomy_order = request.POST.get('taxonomy_order', '').strip()
        size_weight = request.POST.get('size_weight', '').strip()
        diet = request.POST.get('diet', '').strip()
        extinction_era = request.POST.get('extinction_era', '').strip()
        fun_facts = request.POST.get('fun_facts', '').strip()
        taxonomy_extended = request.POST.get('taxonomy_extended', '').strip()
        ecological_impact = request.POST.get('ecological_impact', '').strip()
        conservation_legacy = request.POST.get(
            'conservation_legacy', '').strip()

        # Coordinates for map
        try:
            latitude = float(request.POST.get('latitude', '') or 0) or None
            longitude = float(request.POST.get('longitude', '') or 0) or None
        except (ValueError, TypeError):
            latitude = longitude = None

        # Handle image upload
        image = request.FILES.get('image')

        if not common_name or not binomial_name:
            messages.error(
                request, 'Nome comum e nome científico são obrigatórios.')
            return render(request,
                          'admin_panel/mammal_form.html',
                          {'action': 'add'})

        try:
            mammal = Mammal.objects.create(
                common_name=common_name,
                binomial_name=binomial_name,
                description=description,
                habitat=habitat,
                distribution=distribution,
                extinction_causes=extinction_causes,
                image_filename=image_filename,
                continent=continent,
                taxonomy_order=taxonomy_order,
                size_weight=size_weight,
                diet=diet,
                extinction_era=extinction_era,
                fun_facts=fun_facts,
                taxonomy_extended=taxonomy_extended,
                ecological_impact=ecological_impact,
                conservation_legacy=conservation_legacy,
                latitude=latitude,
                longitude=longitude,
                image=image
            )
            messages.success(
                request, f'Mamífero \"{mammal.common_name}\" adicionado com sucesso!')
            return redirect('mammals:detail', pk=mammal.pk)
        except ValueError as e:
            messages.error(request, f'Erro de validação: {str(e)}')
        except Exception as e:
            messages.error(request, f'Erro ao adicionar mamífero: {str(e)}')

    return render(request, 'admin_panel/mammal_form.html', {'action': 'add'})


@admin_required
def admin_edit_mammal(request, pk):
    """Editar mamífero existente"""
    mammal = get_object_or_404(Mammal, pk=pk)

    if request.method == 'POST':
        mammal.common_name = request.POST.get('common_name', '').strip()
        mammal.binomial_name = request.POST.get('binomial_name', '').strip()
        mammal.description = request.POST.get('description', '').strip()
        mammal.habitat = request.POST.get('habitat', '').strip()
        mammal.distribution = request.POST.get('distribution', '').strip()
        mammal.extinction_causes = request.POST.get(
            'extinction_causes', '').strip()
        mammal.image_filename = request.POST.get('image_filename', '').strip()
        mammal.continent = request.POST.get('continent', '').strip()
        mammal.taxonomy_order = request.POST.get('taxonomy_order', '').strip()
        mammal.size_weight = request.POST.get('size_weight', '').strip()
        mammal.diet = request.POST.get('diet', '').strip()
        mammal.extinction_era = request.POST.get('extinction_era', '').strip()
        mammal.fun_facts = request.POST.get('fun_facts', '').strip()
        mammal.taxonomy_extended = request.POST.get(
            'taxonomy_extended', '').strip()
        mammal.ecological_impact = request.POST.get(
            'ecological_impact', '').strip()
        mammal.conservation_legacy = request.POST.get(
            'conservation_legacy', '').strip()

        # Coordinates for map
        try:
            lat_raw = request.POST.get('latitude', '').strip()
            lon_raw = request.POST.get('longitude', '').strip()
            mammal.latitude = float(lat_raw) if lat_raw else None
            mammal.longitude = float(lon_raw) if lon_raw else None
        except (ValueError, TypeError):
            pass

        # Handle image upload (only override if a file was uploaded)
        if 'image' in request.FILES:
            mammal.image = request.FILES['image']

        if not mammal.common_name or not mammal.binomial_name:
            messages.error(
                request, 'Nome comum e nome científico são obrigatórios.')
            return render(request, 'admin_panel/mammal_form.html', {
                'mammal': mammal,
                'action': 'edit'
            })

        try:
            mammal.save()
            messages.success(
                request, f'Mamífero \"{mammal.common_name}\" atualizado com sucesso!')
            return redirect('mammals:detail', pk=mammal.pk)
        except ValueError as e:
            messages.error(request, f'Erro de validação: {str(e)}')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar mamífero: {str(e)}')

    return render(request, 'admin_panel/mammal_form.html', {
        'mammal': mammal,
        'action': 'edit'
    })


@admin_required
def admin_delete_mammal(request, pk):
    """Deletar mamífero"""
    if request.method == 'POST':
        mammal = get_object_or_404(Mammal, pk=pk)

        try:
            mammal.delete()
            messages.success(request, 'Mamífero removido com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao remover mamífero: {str(e)}')

    return redirect('mammals:admin_mammals')


# ============================================================================
# ADMIN VIEWS - Gestão de Usuários
# ============================================================================

@admin_required
def admin_users(request):
    """Página administrativa de usuários"""
    users = User.objects.select_related('profile').annotate(
        comment_count=Count('comments', distinct=True),
        favorite_count=Count('favorites', distinct=True)
    ).order_by('-date_joined')

    context = {
        'users': users,
    }

    return render(request, 'admin_panel/users.html', context)


@admin_required
def admin_toggle_admin(request, user_id):
    """Alternar status de administrador"""
    if request.method == 'POST':
        if user_id == request.user.id:
            messages.error(
                request,
                'Você não pode alterar seu próprio status de administrador.')
            return redirect('mammals:admin_users')

        user = get_object_or_404(User, pk=user_id)
        profile, created = UserProfile.objects.get_or_create(user=user)

        try:
            profile.is_admin = not profile.is_admin
            profile.save()

            status_text = 'administrador' if profile.is_admin else 'usuário comum'
            messages.success(request, f'Usuário alterado para {status_text}.')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar usuário: {str(e)}')

    return redirect('mammals:admin_users')


@admin_required
def admin_delete_user(request, user_id):
    """Deletar usuário"""
    if request.method == 'POST':
        if user_id == request.user.id:
            messages.error(request, 'Você não pode deletar sua própria conta.')
            return redirect('mammals:admin_users')

        user = get_object_or_404(User, pk=user_id)

        try:
            user.delete()
            messages.success(request, 'Usuário removido com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao remover usuário: {str(e)}')

    return redirect('mammals:admin_users')


# ============================================================================
# COMMENT VIEWS
# ============================================================================

@login_required
def add_comment(request, mammal_id):
    """Adicionar comentário a um mamífero"""
    if request.method == 'POST':
        mammal = get_object_or_404(Mammal, pk=mammal_id)
        content = request.POST.get('content', '').strip()
        scroll_pos = request.POST.get('scroll_pos', '0')

        if not content:
            messages.error(request, _('Comment cannot be empty.'))
            return HttpResponseRedirect(
                reverse(
                    'mammals:detail',
                    args=[mammal_id]) +
                f'?scroll={scroll_pos}#comments-section')

        try:
            Comment.objects.create(
                mammal=mammal,
                user=request.user,
                content=content
            )
            messages.success(request, _('Comment added successfully!'))
        except Exception as e:
            messages.error(
                request,
                _('Error adding comment: {}').format(
                    str(e)))

    return HttpResponseRedirect(
        reverse(
            'mammals:detail',
            args=[mammal_id]) +
        f'?scroll={scroll_pos}#comments-section')


@login_required
def delete_comment(request, comment_id):
    """Deletar comentário"""
    if request.method == 'POST':
        comment = get_object_or_404(Comment, pk=comment_id)
        mammal_id = comment.mammal.id
        scroll_pos = request.POST.get('scroll_pos', '0')

        # Verificar se o usuário é o autor ou admin
        if comment.user == request.user or (
            hasattr(
                request.user,
                'profile') and request.user.profile.is_admin):
            try:
                comment.delete()
                messages.success(request, _('Comment removed successfully!'))
            except Exception as e:
                messages.error(
                    request,
                    _('Error removing comment: {}').format(
                        str(e)))
        else:
            messages.error(
                request,
                _('You do not have permission to delete this comment.'))

        return HttpResponseRedirect(
            reverse(
                'mammals:detail',
                args=[mammal_id]) +
            f'?scroll={scroll_pos}#comments-section')

    return redirect('mammals:index')


# ============================================================================
# FAVORITE VIEWS
# ============================================================================

@login_required
def toggle_favorite(request, mammal_id):
    """Adicionar/remover favorito"""
    if request.method == 'POST':
        mammal = get_object_or_404(Mammal, pk=mammal_id)
        scroll_pos = request.POST.get('scroll_pos', '0')

        try:
            favorite = Favorite.objects.filter(
                user=request.user, mammal=mammal).first()

            if favorite:
                favorite.delete()
                messages.success(request, _('Removed from favorites.'))
            else:
                Favorite.objects.create(user=request.user, mammal=mammal)
                messages.success(request, _('Added to favorites!'))

        except Exception as e:
            messages.error(
                request,
                _('Error updating favorite: {}').format(
                    str(e)))

        # Redirecionar mantendo scroll exato
        return HttpResponseRedirect(
            reverse(
                'mammals:detail',
                args=[mammal_id]) +
            f'?scroll={scroll_pos}#taxonomy-section')

    return redirect('mammals:index')


# ============================================================================
# ERROR HANDLERS
# ============================================================================

def custom_404(request, exception=None):
    """Handler personalizado para erro 404"""
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    """Handler personalizado para erro 500"""
    return render(request, 'errors/500.html', status=500)


def global_map(request):
    """Página do mapa-múndi interativo com heatmap de espécies"""
    return render(request, 'mammals/global_map.html')


def normalize_text(text):
    if not text:
        return ""
    return unicodedata.normalize(
        'NFKD', str(text)).encode(
        'ASCII', 'ignore').decode('utf-8').lower()


def global_map_data(request):
    """Endpoint JSON com dados de todas as espécies para o mapa global"""
    try:
        # Buscar todos os mamíferos do banco de dados - incluindo latitude,
        # longitude e distribuição
        mammals = Mammal.objects.only(
            'id',
            'common_name',
            'binomial_name',
            'continent',
            'image_filename',
            'latitude',
            'longitude',
            'distribution').all()

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
                    'lat': lat,
                    'lon': lon,
                    'location_name': location_name,
                    'species': [],
                    'count': 0
                }

            species_info = {
                'id': mammal.pk,
                'common_name': mammal.common_name,
                'binomial_name': mammal.binomial_name,
                'continent': mammal.continent or 'Unknown',
                'image_filename': mammal.image_filename or ''
            }

            if not any(
                    s['id'] == mammal.pk for s in location_data[location_key]['species']):
                location_data[location_key]['species'].append(species_info)
                location_data[location_key]['count'] += 1

        locations = list(location_data.values())

        # Calcular estatísticas por continente para o heatmap de territórios
        continent_qs = Mammal.objects.only(
            'id', 'common_name', 'binomial_name', 'region', 'image_filename'
        ).all()
        continent_map = {}

        for m in continent_qs:
            reg = (m.region or '').strip()
            if not reg:
                continue

            matched_cont = get_continent_from_region(reg)

            if matched_cont not in continent_map:
                continent_map[matched_cont] = {
                    'continent': matched_cont, 'count': 0, 'species': []}
            continent_map[matched_cont]['count'] += 1
            continent_map[matched_cont]['species'].append({
                'id': m.pk,
                'common_name': m.common_name,
                'binomial_name': m.binomial_name,
                'image_filename': m.image_filename or '',
            })
        continent_stats = list(continent_map.values())

        # Compute stats
        total_locations = len(locations)
        sum(loc['count'] for loc in locations)

        # Max concentration grouped by country/region name
        country_counts = {}
        for loc in locations:
            lname = loc.get('location_name', 'Unknown')
            if lname not in country_counts:
                country_counts[lname] = 0
            country_counts[lname] += loc['count']
        max_concentration = max(country_counts.values(), default=0)
        total_species_all = sum(c['count'] for c in continent_stats)

        response_data = {
            'success': True,
            'locations': locations,
            'continent_stats': continent_stats,
            'total_species': total_species_all,
            'statistics': {
                'total_locations': total_locations,
                'total_species': total_species_all,
                'max_concentration': max_concentration
            }
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def offline(request):
    """Página offline para PWA"""
    return render(request, 'offline.html')


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
            if 'caca' in cause_raw or 'caça' in cause_raw:
                cause_counts['Caça'] += 1
            if 'invasor' in cause_raw:
                cause_counts['Espécies Invasoras'] += 1
            if 'habitat' in cause_raw or 'desmatamento' in cause_raw:
                cause_counts['Perda de Habitat'] += 1
            if 'coloniz' in cause_raw:
                cause_counts['Colonização'] += 1
            if 'clima' in cause_raw:
                cause_counts['Mudança Climática'] += 1

    return JsonResponse({
        'total': total,
        'countries': dict(country_counts),
        'biological_years': dict(biological_year_counts),
        'formalization_years': dict(formalization_year_counts),
        'eras': dict(biological_year_counts),  # backward compat
        'continents': dict(continent_counts),
        'taxonomy': dict(taxonomy_counts),
        'regions': dict(region_counts),
        'causes': dict(cause_counts),
    })


@csrf_exempt
def log_js_error(request):
    try:
        data = json.loads(request.body)
        with open('js_errors.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data) + "\n")
    except json.JSONDecodeError:
        pass
    except IOError:
        pass
    return HttpResponse("OK")
