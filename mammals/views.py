import unicodedata
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import get_language, gettext_lazy as _
from django.urls import reverse
from .models import Mammal, Comment, Favorite
from .decorators import admin_required
from .translation_service import TranslatedMammal
from accounts.models import UserProfile
import json
import re
from collections import Counter
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


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
                        f'/static/images/{
                            mammal.image_filename}' if mammal.image_filename else ''),
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
                request, f'Mamífero "{
                    mammal.common_name}" adicionado com sucesso!')
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
                request, f'Mamífero "{
                    mammal.common_name}" atualizado com sucesso!')
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
                continue

            dist_clean = normalize_text(mammal.distribution)
            country = "Desconhecido"

            if any(
                x in dist_clean for x in [
                    "australia",
                    "gales do sul",
                    "queensland",
                    "victoria",
                    "tasmania",
                    "macquarie",
                    "ilha christmas",
                    "nova gales"]):
                country = "Austrália"
            elif "cuba" in dist_clean:
                country = "Cuba"
            elif any(x in dist_clean for x in ["hispaniola", "republica dominicana", "haiti"]):
                country = "Hispaniola"
            elif "madagascar" in dist_clean:
                country = "Madagascar"
            elif "japao" in dist_clean or "japan" in dist_clean:
                country = "Japão"
            elif "mexico" in dist_clean:
                country = "México"
            elif "brasil" in dist_clean:
                country = "Brasil"
            elif "indonesia" in dist_clean:
                country = "Indonésia"
            elif any(x in dist_clean for x in ["nova zelandia", "new zealand", "maori"]):
                country = "Nova Zelândia"
            elif any(x in dist_clean for x in ["caribe", "porto rico", "jamaica", "barbuda", "antinhas", "antilhas"]):
                country = "Ilhas do Caribe"
            elif "salomao" in dist_clean:
                country = "Ilhas Salomão"
            elif "argentina" in dist_clean:
                country = "Argentina"
            elif "peru" in dist_clean:
                country = "Peru"
            elif "colombia" in dist_clean:
                country = "Colômbia"
            elif "chile" in dist_clean:
                country = "Chile"
            elif "falkland" in dist_clean or "malvinas" in dist_clean:
                country = "Ilhas Malvinas"
            elif "galapagos" in dist_clean or "equador" in dist_clean:
                country = "Equador (Galápagos)"
            elif "mauricio" in dist_clean or "reuniao" in dist_clean or "rodrigues" in dist_clean:
                country = "Ilhas Mascarenhas"
            elif "argelia" in dist_clean or "marrocos" in dist_clean or "norte da africa" in dist_clean:
                country = "Norte da África"
            elif "russia" in dist_clean or "siberia" in dist_clean:
                country = "Rússia"
            elif "canada" in dist_clean:
                country = "Canadá"
            elif any(x in dist_clean for x in ["estados unidos", "eua", "california", "texas"]):
                country = "Estados Unidos"
            else:
                # Fallback
                parts = str(mammal.distribution).split(',')
                if len(parts) > 1:
                    country = parts[-1].split('(')[0].strip()
                else:
                    country = str(mammal.distribution).split('(')[0].strip()

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
        continent_qs = (
            Mammal.objects .only(
                'id',
                'common_name',
                'binomial_name',
                'continent',
                'image_filename') .exclude(
                continent__isnull=True) .exclude(
                continent__exact=''))
        continent_map = {}

        valid_continents = {
            'América do Norte': 'América do Norte',
            'North America': 'América do Norte',
            'América do Sul': 'América do Sul',
            'South America': 'América do Sul',
            'Europa': 'Europa',
            'Europe': 'Europa',
            'Ásia': 'Ásia',
            'Asia': 'Ásia',
            'África': 'África',
            'Africa': 'África',
            'Oceania': 'Oceania',
            'Australia': 'Oceania',
        }

        for m in continent_qs:
            cont_raw = (m.continent or '').strip()
            if not cont_raw:
                continue

            matched_cont = None
            for k, v in valid_continents.items():
                if k.lower() in cont_raw.lower():
                    matched_cont = v
                    break

            if not matched_cont:
                if 'américa' in cont_raw.lower() or 'america' in cont_raw.lower():
                    matched_cont = 'América do Norte'
                else:
                    continue  # Skip se não for continente válido

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
    era_counts = Counter()
    continent_counts = Counter()
    taxonomy_counts = Counter()

    total = mammals.count()

    for m in mammals:
        # 1. Countries
        if m.distribution:
            dist_clean = normalize_text(m.distribution)
            country = "Desconhecido"

            if any(
                x in dist_clean for x in [
                    "australia",
                    "gales do sul",
                    "queensland",
                    "victoria",
                    "tasmania",
                    "macquarie",
                    "ilha christmas",
                    "nova gales"]):
                country = "Austrália"
            elif "cuba" in dist_clean:
                country = "Cuba"
            elif any(x in dist_clean for x in ["hispaniola", "republica dominicana", "haiti"]):
                country = "Hispaniola"
            elif "madagascar" in dist_clean:
                country = "Madagascar"
            elif "japao" in dist_clean or "japan" in dist_clean:
                country = "Japão"
            elif "mexico" in dist_clean:
                country = "México"
            elif "brasil" in dist_clean:
                country = "Brasil"
            elif "indonesia" in dist_clean:
                country = "Indonésia"
            elif any(x in dist_clean for x in ["nova zelandia", "new zealand", "maori"]):
                country = "Nova Zelândia"
            elif any(x in dist_clean for x in ["caribe", "porto rico", "jamaica", "barbuda", "antinhas", "antilhas"]):
                country = "Ilhas do Caribe"
            elif "salomao" in dist_clean:
                country = "Ilhas Salomão"
            elif "argentina" in dist_clean:
                country = "Argentina"
            elif "peru" in dist_clean:
                country = "Peru"
            elif "colombia" in dist_clean:
                country = "Colômbia"
            elif "chile" in dist_clean:
                country = "Chile"
            elif "falkland" in dist_clean or "malvinas" in dist_clean:
                country = "Ilhas Malvinas"
            elif "galapagos" in dist_clean or "equador" in dist_clean:
                country = "Equador (Galápagos)"
            elif "mauricio" in dist_clean or "reuniao" in dist_clean or "rodrigues" in dist_clean:
                country = "Ilhas Mascarenhas"
            elif "argelia" in dist_clean or "marrocos" in dist_clean or "norte da africa" in dist_clean:
                country = "Norte da África"
            elif "russia" in dist_clean or "siberia" in dist_clean:
                country = "Rússia"
            elif "canada" in dist_clean:
                country = "Canadá"
            elif any(x in dist_clean for x in ["estados unidos", "eua", "california", "texas"]):
                country = "Estados Unidos"
            else:
                # Fallback
                parts = str(m.distribution).split(',')
                if len(parts) > 1:
                    country = parts[-1].split('(')[0].strip()
                else:
                    country = str(m.distribution).split('(')[0].strip()

            country_counts[country] += 1

        # 2. Era (agrupada por Ano Exato para o gráfico de curva temporal)
        if m.extinction_era:
            era_raw = m.extinction_era.lower()
            parsed_year = None

            # Buscar anos exatos (ex: 1931 -> 1931)
            years = re.findall(r'\b(1[5-9]\d\d|20\d\d)\b', era_raw)
            if years:
                parsed_year = int(years[-1])
            else:
                # Estimativas se tiver apenas o século
                if 'xvi' in era_raw or '16' in era_raw:
                    parsed_year = 1550
                elif 'xvii' in era_raw or '17' in era_raw:
                    parsed_year = 1650
                elif 'xviii' in era_raw or '18' in era_raw:
                    parsed_year = 1750
                elif 'xix' in era_raw or '19' in era_raw:
                    parsed_year = 1850
                elif 'xx' in era_raw or '20' in era_raw:
                    parsed_year = 1950
                elif 'xxi' in era_raw or '21' in era_raw:
                    parsed_year = 2010
                elif 'holoceno' in era_raw:
                    parsed_year = 1500
                elif 'pleistoceno' in era_raw:
                    parsed_year = 1500

            if parsed_year and parsed_year >= 1500:
                era_counts[str(parsed_year)] += 1

        # 3. Continent
        if m.continent:
            cont = m.continent.strip()
            valid_continents = {
                'América do Norte': 'América do Norte',
                'North America': 'América do Norte',
                'América do Sul': 'América do Sul',
                'South America': 'América do Sul',
                'Europa': 'Europa',
                'Europe': 'Europa',
                'Ásia': 'Ásia',
                'Asia': 'Ásia',
                'África': 'África',
                'Africa': 'África',
                'Oceania': 'Oceania',
                'Australia': 'Oceania',
            }
            matched = False
            for k, v in valid_continents.items():
                if k.lower() in cont.lower():
                    continent_counts[v] += 1
                    matched = True
                    break
            if not matched:
                if 'américa' in cont.lower() or 'america' in cont.lower():
                    continent_counts['América do Norte'] += 1

        # 4. Taxonomy
        if m.taxonomy_order:
            taxonomy_counts[m.taxonomy_order] += 1

    return JsonResponse({
        'total': total,
        'countries': dict(country_counts),
        'eras': dict(era_counts),
        'continents': dict(continent_counts),
        'taxonomy': dict(taxonomy_counts)
    })


@csrf_exempt
def log_js_error(request):
    try:
        data = json.loads(request.body)
        with open('js_errors.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data) + "\n")
    except Exception:
        pass
    return HttpResponse("OK")
