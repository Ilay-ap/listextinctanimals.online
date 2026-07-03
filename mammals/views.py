import json
import unicodedata
from collections import Counter

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit

from accounts.models import UserProfile

from .decorators import admin_required
from .models import Comment, Favorite, Mammal
from .translation_service import TranslatedMammal

User = get_user_model()


from .constants import COUNTRY_MAP

def get_country_from_distribution(distribution):
    """Retorna o país ou região baseado no campo distribution"""
    dist_clean = normalize_text(distribution)

    for keys, val in COUNTRY_MAP.items():
        if any(k in dist_clean for k in keys):
            return val

    # Fallback
    parts = str(distribution).split(",", maxsplit=1)
    return (
        parts[-1].split("(", maxsplit=1)[0].strip()
        if len(parts) > 1
        else str(distribution).split("(", maxsplit=1)[0].strip()
    )


def get_continent_from_region(region):
    """Mapeia as regiões simplificadas para os continentes"""
    reg = str(region or "").strip()
    if not reg:
        return "Unknown"

    if "Americas" in reg or "Caribe" in reg:
        return "Américas"
    if "Asia" in reg:
        return "Ásia"
    if "Europa" in reg:
        return "Europa"
    if "Oceano" in reg or "Australia" in reg:
        return "Oceania"
    if "Madagascar" in reg or "Africa" in reg:
        return "África"
    return reg


def index(request):
    """Página inicial com lista de mamíferos"""
    # Otimizar query - carregar apenas campos necessários
    mammals_list = Mammal.objects.only(
        "id",
        "common_name",
        "binomial_name",
        "description",
        "image",
        "image_filename",
        "continent",
        "taxonomy_order",
    ).all()

    # Paginação - 24 mamíferos por página
    paginator = Paginator(mammals_list, 24)
    page = request.GET.get("page", 1)

    try:
        mammals = paginator.page(page)
    except PageNotAnInteger:
        mammals = paginator.page(1)
    except EmptyPage:
        mammals = paginator.page(paginator.num_pages)

    # Traduzir mamíferos para o idioma atual
    from .utils import get_normalized_lang_code
    lang_code = get_normalized_lang_code()
    current_lang = get_language()
    
    if lang_code != 'pt':
        mammals.object_list = [
            TranslatedMammal(m, current_lang) for m in mammals.object_list
        ]

    # Obter favoritos do usuário se autenticado
    favorites = []
    if request.user.is_authenticated:
        favorites = list(request.user.favorites.values_list("mammal_id", flat=True))

    context = {
        "mammals": mammals,
        "favorites": favorites,
        "is_paginated": paginator.num_pages > 1,
    }

    return render(request, "mammals/index.html", context)


def mammal_detail(request, pk):
    """Página de detalhes de um mamífero"""

    # Otimizar query - carregar comentários com usuários em uma query
    mammal_obj = get_object_or_404(
        Mammal.objects.prefetch_related("comments__user"), pk=pk
    )

    # Traduzir mamífero para o idioma atual
    from .utils import get_normalized_lang_code
    lang_code = get_normalized_lang_code()
    current_lang = get_language()
    
    if lang_code != 'pt':
        mammal = TranslatedMammal(mammal_obj, current_lang)
    else:
        mammal = mammal_obj

    comments = (
        mammal.mammal.comments.select_related("user").all()
        if hasattr(mammal, "mammal")
        else mammal.comments.select_related("user").all()
    )

    # Verificar se é favorito (sempre usar mammal_obj original)
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(
            user=request.user, mammal=mammal_obj
        ).exists()

    # Obter coordenadas diretamente do banco de dados (já auditado)
    map_data = None
    if mammal_obj.latitude is not None and mammal_obj.longitude is not None:
        location_name = "Desconhecido"
        if mammal_obj.distribution:
            location_name = str(mammal_obj.distribution).split(",")[0].strip()

        map_data = {
            "coordinates": [
                {
                    "lat": mammal_obj.latitude,
                    "lon": mammal_obj.longitude,
                    "location": location_name,
                }
            ],
            "center": {"lat": mammal_obj.latitude, "lon": mammal_obj.longitude},
            "zoom": 5,
        }

    geo_country = ""
    if mammal_obj.distribution:
        geo_country = get_country_from_distribution(mammal_obj.distribution)

    context = {
        "mammal": mammal,
        "comments": comments,
        "is_favorite": is_favorite,
        "map_data": json.dumps(map_data) if map_data else None,
        "geo_country": geo_country,
    }

    return render(request, "mammals/detail.html", context)


def about(request):
    """Página sobre o projeto"""
    return render(request, "mammals/about.html")


@login_required
def favorites_view(request):
    """Página de favoritos do usuário"""
    favorites = request.user.favorites.select_related("mammal").all()

    # Traduzir mamíferos favoritos
    from .utils import get_normalized_lang_code
    lang_code = get_normalized_lang_code()
    current_lang = get_language()

    # Criar lista de mamíferos traduzidos para o template
    mammals_list = []
    for fav in favorites:
        if lang_code != "pt":
            mammal = TranslatedMammal(fav.mammal, current_lang)
        else:
            mammal = fav.mammal
        mammals_list.append({"favorite": fav, "mammal": mammal})

    context = {
        "favorites": mammals_list,
    }

    return render(request, "mammals/favorites.html", context)




# ============================================================================
# ADMIN VIEWS - CRUD de Mamíferos
# ============================================================================


@admin_required
def admin_mammals(request):
    """Página administrativa de mamíferos"""
    mammals = Mammal.objects.all()

    context = {
        "mammals": mammals,
    }

    return render(request, "admin_panel/mammals.html", context)


@admin_required
def admin_add_mammal(request):
    """Adicionar novo mamífero"""
    if request.method == "POST":
        common_name = request.POST.get("common_name", "").strip()
        binomial_name = request.POST.get("binomial_name", "").strip()
        description = request.POST.get("description", "").strip()
        habitat = request.POST.get("habitat", "").strip()
        distribution = request.POST.get("distribution", "").strip()
        extinction_causes = request.POST.get("extinction_causes", "").strip()
        image_filename = request.POST.get("image_filename", "").strip()
        continent = request.POST.get("continent", "").strip()
        taxonomy_order = request.POST.get("taxonomy_order", "").strip()
        size_weight = request.POST.get("size_weight", "").strip()
        diet = request.POST.get("diet", "").strip()
        extinction_era = request.POST.get("extinction_era", "").strip()
        fun_facts = request.POST.get("fun_facts", "").strip()
        taxonomy_extended = request.POST.get("taxonomy_extended", "").strip()
        ecological_impact = request.POST.get("ecological_impact", "").strip()
        conservation_legacy = request.POST.get("conservation_legacy", "").strip()

        # Coordinates for map
        try:
            latitude = float(request.POST.get("latitude", "") or 0) or None
            longitude = float(request.POST.get("longitude", "") or 0) or None
        except (ValueError, TypeError):
            latitude = longitude = None

        # Handle image upload
        image = request.FILES.get("image")

        if not common_name or not binomial_name:
            messages.error(request, "Nome comum e nome científico são obrigatórios.")
            return render(request, "admin_panel/mammal_form.html", {"action": "add"})

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
                image=image,
            )
            messages.success(
                request, f'Mamífero "{mammal.common_name}" adicionado com sucesso!'
            )
            return redirect("mammals:detail", pk=mammal.pk)
        except ValueError as e:
            messages.error(request, f"Erro de validação: {str(e)}")
        except Exception as e:
            messages.error(request, f"Erro ao adicionar mamífero: {str(e)}")

    return render(request, "admin_panel/mammal_form.html", {"action": "add"})


@admin_required
def admin_edit_mammal(request, pk):
    """Editar mamífero existente"""
    mammal = get_object_or_404(Mammal, pk=pk)

    if request.method == "POST":
        mammal.common_name = request.POST.get("common_name", "").strip()
        mammal.binomial_name = request.POST.get("binomial_name", "").strip()
        mammal.description = request.POST.get("description", "").strip()
        mammal.habitat = request.POST.get("habitat", "").strip()
        mammal.distribution = request.POST.get("distribution", "").strip()
        mammal.extinction_causes = request.POST.get("extinction_causes", "").strip()
        mammal.image_filename = request.POST.get("image_filename", "").strip()
        mammal.continent = request.POST.get("continent", "").strip()
        mammal.taxonomy_order = request.POST.get("taxonomy_order", "").strip()
        mammal.size_weight = request.POST.get("size_weight", "").strip()
        mammal.diet = request.POST.get("diet", "").strip()
        mammal.extinction_era = request.POST.get("extinction_era", "").strip()
        mammal.fun_facts = request.POST.get("fun_facts", "").strip()
        mammal.taxonomy_extended = request.POST.get("taxonomy_extended", "").strip()
        mammal.ecological_impact = request.POST.get("ecological_impact", "").strip()
        mammal.conservation_legacy = request.POST.get("conservation_legacy", "").strip()

        # Coordinates for map
        try:
            lat_raw = request.POST.get("latitude", "").strip()
            lon_raw = request.POST.get("longitude", "").strip()
            mammal.latitude = float(lat_raw) if lat_raw else None
            mammal.longitude = float(lon_raw) if lon_raw else None
        except (ValueError, TypeError):
            pass

        # Handle image upload (only override if a file was uploaded)
        if "image" in request.FILES:
            mammal.image = request.FILES["image"]

        if not mammal.common_name or not mammal.binomial_name:
            messages.error(request, "Nome comum e nome científico são obrigatórios.")
            return render(
                request,
                "admin_panel/mammal_form.html",
                {"mammal": mammal, "action": "edit"},
            )

        try:
            mammal.save()
            messages.success(
                request, f'Mamífero "{mammal.common_name}" atualizado com sucesso!'
            )
            return redirect("mammals:detail", pk=mammal.pk)
        except ValueError as e:
            messages.error(request, f"Erro de validação: {str(e)}")
        except Exception as e:
            messages.error(request, f"Erro ao atualizar mamífero: {str(e)}")

    return render(
        request, "admin_panel/mammal_form.html", {"mammal": mammal, "action": "edit"}
    )


@admin_required
def admin_delete_mammal(request, pk):
    """Deletar mamífero"""
    if request.method == "POST":
        mammal = get_object_or_404(Mammal, pk=pk)

        try:
            mammal.delete()
            messages.success(request, "Mamífero removido com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro ao remover mamífero: {str(e)}")

    return redirect("mammals:admin_mammals")


# ============================================================================
# ADMIN VIEWS - Gestão de Usuários
# ============================================================================


@admin_required
def admin_users(request):
    """Página administrativa de usuários"""
    users = (
        User.objects.select_related("profile")
        .annotate(
            comment_count=Count("comments", distinct=True),
            favorite_count=Count("favorites", distinct=True),
        )
        .order_by("-date_joined")
    )

    context = {
        "users": users,
    }

    return render(request, "admin_panel/users.html", context)


@admin_required
def admin_toggle_admin(request, user_id):
    """Alternar status de administrador"""
    if request.method == "POST":
        if user_id == request.user.id:
            messages.error(
                request, "Você não pode alterar seu próprio status de administrador."
            )
            return redirect("mammals:admin_users")

        user = get_object_or_404(User, pk=user_id)
        profile, created = UserProfile.objects.get_or_create(user=user)

        try:
            profile.is_admin = not profile.is_admin
            profile.save()

            status_text = "administrador" if profile.is_admin else "usuário comum"
            messages.success(request, f"Usuário alterado para {status_text}.")
        except Exception as e:
            messages.error(request, f"Erro ao atualizar usuário: {str(e)}")

    return redirect("mammals:admin_users")


@admin_required
def admin_delete_user(request, user_id):
    """Deletar usuário"""
    if request.method == "POST":
        if user_id == request.user.id:
            messages.error(request, "Você não pode deletar sua própria conta.")
            return redirect("mammals:admin_users")

        user = get_object_or_404(User, pk=user_id)

        try:
            user.delete()
            messages.success(request, "Usuário removido com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro ao remover usuário: {str(e)}")

    return redirect("mammals:admin_users")


# ============================================================================
# COMMENT VIEWS
# ============================================================================


@login_required
@ratelimit(key="ip", rate="20/m", block=True)
def add_comment(request, mammal_id):
    """Adicionar comentário a um mamífero"""
    if request.method == "POST":
        mammal = get_object_or_404(Mammal, pk=mammal_id)
        content = request.POST.get("content", "").strip()
        scroll_pos = request.POST.get("scroll_pos", "0")

        if not content:
            messages.error(request, _("Comment cannot be empty."))
            return HttpResponseRedirect(
                reverse("mammals:detail", args=[mammal_id])
                + f"?scroll={scroll_pos}#comments-section"
            )

        try:
            Comment.objects.create(mammal=mammal, user=request.user, content=content)
            messages.success(request, _("Comment added successfully!"))
        except Exception as e:
            messages.error(request, _("Error adding comment: {}").format(str(e)))

    return HttpResponseRedirect(
        reverse("mammals:detail", args=[mammal_id])
        + f"?scroll={scroll_pos}#comments-section"
    )


@login_required
def delete_comment(request, comment_id):
    """Deletar comentário"""
    if request.method == "POST":
        comment = get_object_or_404(Comment, pk=comment_id)
        mammal_id = comment.mammal.id
        scroll_pos = request.POST.get("scroll_pos", "0")

        # Verificar se o usuário é o autor ou admin
        if comment.user == request.user or (
            hasattr(request.user, "profile") and request.user.profile.is_admin
        ):
            try:
                comment.delete()
                messages.success(request, _("Comment removed successfully!"))
            except Exception as e:
                messages.error(request, _("Error removing comment: {}").format(str(e)))
        else:
            messages.error(
                request, _("You do not have permission to delete this comment.")
            )

        return HttpResponseRedirect(
            reverse("mammals:detail", args=[mammal_id])
            + f"?scroll={scroll_pos}#comments-section"
        )

    return redirect("mammals:index")


# ============================================================================
# FAVORITE VIEWS
# ============================================================================


@login_required
@ratelimit(key="ip", rate="20/m", block=True)
def toggle_favorite(request, mammal_id):
    """Adicionar/remover favorito"""
    if request.method == "POST":
        mammal = get_object_or_404(Mammal, pk=mammal_id)
        scroll_pos = request.POST.get("scroll_pos", "0")

        try:
            favorite = Favorite.objects.filter(user=request.user, mammal=mammal).first()

            if favorite:
                favorite.delete()
                messages.success(request, _("Removed from favorites."))
            else:
                Favorite.objects.create(user=request.user, mammal=mammal)
                messages.success(request, _("Added to favorites!"))

        except Exception as e:
            messages.error(request, _("Error updating favorite: {}").format(str(e)))

        # Redirecionar mantendo scroll exato
        return HttpResponseRedirect(
            reverse("mammals:detail", args=[mammal_id])
            + f"?scroll={scroll_pos}#taxonomy-section"
        )

    return redirect("mammals:index")


# ============================================================================
# ERROR HANDLERS
# ============================================================================


def custom_404(request, exception=None):
    """Handler personalizado para erro 404"""
    return render(request, "errors/404.html", status=404)


def custom_500(request):
    """Handler personalizado para erro 500"""
    return render(request, "errors/500.html", status=500)


def global_map(request):
    """Página do mapa-múndi interativo com heatmap de espécies"""
    return render(request, "mammals/global_map.html")


def normalize_text(text):
    if not text:
        return ""
    return (
        unicodedata.normalize("NFKD", str(text))
        .encode("ASCII", "ignore")
        .decode("utf-8")
        .lower()
    )




def offline(request):
    """Página offline para PWA"""
    return render(request, "offline.html")


