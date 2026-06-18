import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = [".jpg", ".jpeg", ".png", ".webp"]
    if not ext.lower() in valid_extensions:
        raise ValidationError(
            "Extensão de arquivo não suportada. Apenas JPG, PNG ou WEBP são permitidos."
        )


def safe_mammal_image_path(instance, filename):
    """Gera um nome de arquivo seguro via UUID mitigando ataques de Path Traversal"""
    # pylint: disable=unused-argument
    ext = filename.split(".")[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join("mammals", filename)


from django.db.models import Q

class MammalManager(models.Manager):
    def search_api(self, query, region_filter, taxonomy_filter):
        qs = self.only(
            "id", "common_name", "binomial_name", "description",
            "image", "image_filename", "continent", "taxonomy_order"
        )
        if query:
            qs = qs.filter(
                Q(common_name__icontains=query) |
                Q(binomial_name__icontains=query) |
                Q(description__icontains=query)
            )
        if region_filter and region_filter.lower() != "all":
            qs = qs.filter(continent__iexact=region_filter)
        if taxonomy_filter and taxonomy_filter.upper() != "ALL":
            qs = qs.filter(taxonomy_order__iexact=taxonomy_filter)
        return qs

class Mammal(models.Model):
    objects = MammalManager()

    """Modelo para mamíferos extintos"""

    common_name = models.CharField(
        max_length=200, verbose_name="Nome Comum", help_text="Nome popular do mamífero"
    )
    binomial_name = models.CharField(
        max_length=200,
        verbose_name="Nome Científico",
        help_text="Nome binomial (científico) do mamífero",
    )
    description = models.TextField(
        verbose_name="Descrição", help_text="Descrição detalhada do mamífero"
    )
    habitat = models.TextField(
        blank=True,
        null=True,
        verbose_name="Habitat",
        help_text="Habitat natural do mamífero",
    )
    distribution = models.TextField(
        blank=True,
        null=True,
        verbose_name="Distribução",
        help_text="Distribuição geográfica",
    )
    extinction_causes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Causas da Extinção",
        help_text="Principais causas que levaram à extinção",
    )
    image_filename = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nome Herança Antigo",
        help_text="Nome do arquivo de imagem na pasta static/images (Legado)",
    )
    image = models.ImageField(
        upload_to=safe_mammal_image_path,
        blank=True,
        null=True,
        validators=[validate_image_extension],
        verbose_name="Foto/Imagem Oficial",
        help_text="Faça upload de uma foto para o mamífero",
    )
    size_weight = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Tamanho e Peso",
        help_text="Ex: 1,5m de altura, 200kg",
    )
    diet = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Dieta",
        help_text="O que este animal comia? (ex: Herbívoro, Carnívoro...)",
    )
    extinction_era = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Época da Extinção",
        help_text="Quando foi visto pela última vez? (ex: Anos 1930, Século XVII)",
    )
    fun_facts = models.TextField(
        blank=True,
        null=True,
        verbose_name="Curiosidades",
        help_text="Fatos ou observações interessantes adicionais",
    )
    taxonomy_extended = models.TextField(
        blank=True,
        null=True,
        verbose_name="Taxonomia Estendida",
        help_text="Família, Gênero e outras informações taxonômicas adicionais",
    )
    ecological_impact = models.TextField(
        blank=True,
        null=True,
        verbose_name="Impacto Ecológico",
        help_text="Papel deste animal no ecossistema e impacto de sua extinção",
    )
    conservation_legacy = models.TextField(
        blank=True,
        null=True,
        verbose_name="Conservação e Legado",
        help_text="Museus, registros históricos, esforços de conservação e importância cultural",
    )
    scientific_references = models.TextField(
        blank=True,
        null=True,
        verbose_name="Referências Científicas",
        help_text="Referências bibliográficas e científicas da espécie",
    )
    extinction_year = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Ano de Extinção Biológica",
        help_text="Último registro vivo confirmado (ano)",
    )
    formalization_year = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Ano de Formalização",
        help_text="Ano da declaração formal de extinção (IUCN ou literatura)",
    )
    formalization_source = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Fonte da Formalização",
        help_text="Ex: IUCN 2008, lit. 1903",
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Região",
        help_text="Região geográfica (Americas, Caribe, Australia, etc.)",
    )
    main_cause = models.TextField(
        blank=True,
        null=True,
        verbose_name="Causa Principal",
        help_text="Causa principal da extinção",
    )
    continent = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Continente",
        help_text="Continente onde o mamífero habitava",
    )
    taxonomy_order = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Ordem Taxonômica",
        help_text="Ordem taxonômica do mamífero",
    )
    latitude = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Latitude",
        help_text="Coordenada de latitude para posição no mapa",
    )
    longitude = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Longitude",
        help_text="Coordenada de longitude para posição no mapa",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Mamífero Extinto"
        verbose_name_plural = "Mamíferos Extintos"
        ordering = ["common_name"]
        indexes = [
            models.Index(fields=["common_name"]),
            models.Index(fields=["continent"]),
            models.Index(fields=["taxonomy_order"]),
            models.Index(fields=["extinction_year"]),
            models.Index(fields=["formalization_year"]),
            models.Index(fields=["-updated_at"]),
        ]

    def __str__(self):
        return f"{self.common_name} ({self.binomial_name})"

    def get_absolute_url(self):
        return reverse("mammals:detail", kwargs={"pk": self.pk})

    @property
    def gallery_images(self):
        """Retorna imagens adicionais da galeria para o auroque."""
        media_path = os.path.join(settings.MEDIA_ROOT, "mammals")
        if not os.path.exists(media_path):
            return []

        files = os.listdir(media_path)
        images = []

        if str(self.binomial_name).lower() == "bos primigenius":
            prefixes = [
                "02_",
                "03_",
                "04_",
                "05_",
                "06_",
                "08_",
                "09_",
                "10_",
                "11_",
                "12_",
                "13_",
                "14_",
                "15_",
            ]
            for f in files:
                if any(f.startswith(p) for p in prefixes) and f.lower().endswith(
                    (".jpg", ".jpeg", ".png", ".webp")
                ):
                    images.append(
                        {
                            "url": f"{settings.MEDIA_URL}mammals/{f}",
                            "filename": f,
                            "caption": self._get_caption_for_file(f),
                        }
                    )
        return sorted(images, key=lambda x: x["url"])

    def _get_caption_for_file(self, filename):
        captions = {
            "02_esqueleto_leste_asiatico.jpg": "Esqueleto fóssil de auroque encontrado no Leste Asiático.",
            "03_esqueleto_7500_anos.jpg": "Esqueleto fóssil completo de auroque datado de aproximadamente 7.500 anos.",
            "04_cranio_chifres_1.jpg": "Crânio fóssil com chifres - Estudo Anatômico Lateral.",
            "05_cranio_museu_alta_resolucao.jpg": "Crânio de auroque exposto em museu (Alta Resolução).",
            "06_cranio_chifres_2.jpg": "Crânio fóssil com chifres - Estudo Anatômico Frontal.",
            "08_cranio_chifres_3.jpg": "Crânio fóssil com chifres - Estudo Anatômico Superior.",
            "09_cranio_chifres_completos.jpg": "Crânio e chifres completos preservados exibindo a curvatura em lira.",
            "10_cranio_atlas_obscura.jpg": "Crânio histórico de auroque catalogado no Atlas Obscura.",
            "11_cranio_inusual.jpg": "Crânio fóssil de auroque apresentando uma curvatura inusual de chifre.",
            "12_cranio_premium.jpg": "Crânio fóssil de auroque de alta qualidade de preservação em museu.",
            "13_mandibula_dentes_alta_resolucao.jpg": "Mandíbula fóssil com dentes molares preservados em alta resolução.",
            "14_mandibula_isolada.jpg": "Mandíbula fóssil isolada para análise paleontológica.",
            "15_chifre_ultimo_auroque_1620.jpg": "Corno de caça esculpido a partir do chifre do último auroque vivo (datado de 1620).",
        }
        return captions.get(filename, "Imagem do Auroque")

    @property
    def short_description(self):
        """Retorna uma versão curta da descrição"""
        desc = str(self.description)
        if len(desc) > 200:
            return desc[:200] + "..."
        return desc


class Comment(models.Model):
    """Modelo para comentários em mamíferos"""

    mammal = models.ForeignKey(
        Mammal,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Mamífero",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="Usuário que fez o comentário",
    )
    content = models.TextField(
        verbose_name="Conteúdo", help_text="Conteúdo do comentário"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Comentário"
        verbose_name_plural = "Comentários"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mammal", "-created_at"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"Comentário de {self.user.username} em {self.mammal.common_name}"


class Favorite(models.Model):
    """Modelo para favoritos (relação N:N entre usuários e mamíferos)"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        help_text="Usuário que favoritou",
    )
    mammal = models.ForeignKey(
        Mammal,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="Mamífero",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Favoritado em")

    class Meta:
        verbose_name = "Favorito"
        verbose_name_plural = "Favoritos"
        ordering = ["-created_at"]
        unique_together = ["user", "mammal"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["mammal"]),
        ]

    def __str__(self):
        return f"{self.user.username} favoritou {self.mammal.common_name}"
