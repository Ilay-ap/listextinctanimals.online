"""
Testes de Banco de Dados - test_database.py

Testa operações de banco de dados:
- Buscar mamífero por ID
- Listar todos os mamíferos
- Queries complexas
- Integridade de dados
"""

import pytest
from django.test import Client
from django.contrib.auth.models import User
from mammals.models import Mammal, Comment, Favorite
from accounts.models import UserProfile
from django.db.models import Count


@pytest.mark.django_db
class TestDatabaseOperations:
    """Classe de testes para operações de banco de dados"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        # Criar múltiplos mamíferos para testes
        self.mammal1 = Mammal.objects.create(
            common_name="Tilacino",
            binomial_name="Thylacinus cynocephalus",
            description="Carnívoro marsupial da Tasmânia",
            continent="Oceania",
            taxonomy_order="DASYUROMORPHIA"
        )
        
        self.mammal2 = Mammal.objects.create(
            common_name="Auroch",
            binomial_name="Bos primigenius",
            description="Ancestral do gado doméstico",
            continent="Europe",
            taxonomy_order="ARTIODACTYLA"
        )
        
        self.mammal3 = Mammal.objects.create(
            common_name="Leão-do-Atlas",
            binomial_name="Panthera leo leo",
            description="Subespécie de leão do Norte da África",
            continent="Africa",
            taxonomy_order="CARNIVORA"
        )
    
    def test_fetch_mammal_by_id(self):
        """
        Teste 1: Buscar mamífero por ID funciona
        Verifica se é possível buscar um mamífero específico por ID
        """
        # Buscar mamífero por ID
        mammal = Mammal.objects.get(pk=self.mammal1.pk)
        
        # Verificar dados
        assert mammal is not None
        assert mammal.common_name == "Tilacino"
        assert mammal.binomial_name == "Thylacinus cynocephalus"
        assert mammal.continent == "Oceania"
        assert mammal.taxonomy_order == "DASYUROMORPHIA"
    
    def test_list_all_mammals(self):
        """
        Teste 2: Listar todos os mamíferos retorna lista
        Verifica se é possível listar todos os mamíferos
        """
        # Buscar todos os mamíferos
        mammals = Mammal.objects.all()
        
        # Verificar quantidade
        assert mammals.count() == 3
        
        # Verificar que todos foram criados
        mammal_names = [m.common_name for m in mammals]
        assert "Tilacino" in mammal_names
        assert "Auroch" in mammal_names
        assert "Leão-do-Atlas" in mammal_names


@pytest.mark.django_db
class TestDatabaseQueries:
    """Testes para queries complexas de banco de dados"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup com dados mais complexos"""
        # Criar mamíferos
        self.mammal1 = Mammal.objects.create(
            common_name="Tigre-de-Java",
            binomial_name="Panthera tigris sondaica",
            description="Subespécie de tigre extinta de Java",
            continent="Asia",
            taxonomy_order="CARNIVORA"
        )
        
        self.mammal2 = Mammal.objects.create(
            common_name="Foca-monge-do-Caribe",
            binomial_name="Neomonachus tropicalis",
            description="Foca extinta do Caribe",
            continent="America",
            taxonomy_order="CARNIVORA"
        )
        
        # Criar usuários
        self.user1 = User.objects.create_user(
            username='user1',
            password='senha123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            password='senha123'
        )
    
    def test_filter_by_continent(self):
        """Testa filtro por continente"""
        # Buscar mamíferos da Ásia
        asia_mammals = Mammal.objects.filter(continent="Asia")
        
        assert asia_mammals.count() == 1
        assert asia_mammals.first().common_name == "Tigre-de-Java"
    
    def test_filter_by_taxonomy(self):
        """Testa filtro por ordem taxonômica"""
        # Buscar carnívoros
        carnivores = Mammal.objects.filter(taxonomy_order="CARNIVORA")
        
        assert carnivores.count() == 2
        carnivore_names = [m.common_name for m in carnivores]
        assert "Tigre-de-Java" in carnivore_names
        assert "Foca-monge-do-Caribe" in carnivore_names
    
    def test_search_by_name(self):
        """Testa busca por nome (case-insensitive)"""
        # Buscar por "tigre"
        results = Mammal.objects.filter(common_name__icontains="tigre")
        
        assert results.count() == 1
        assert results.first().common_name == "Tigre-de-Java"
    
    def test_search_by_binomial_name(self):
        """Testa busca por nome científico"""
        # Buscar por "Panthera"
        results = Mammal.objects.filter(binomial_name__icontains="Panthera")
        
        assert results.count() == 1
        assert results.first().binomial_name == "Panthera tigris sondaica"
    
    def test_mammal_with_comments_count(self):
        """Testa contagem de comentários por mamífero"""
        # Adicionar comentários
        Comment.objects.create(
            mammal=self.mammal1,
            user=self.user1,
            content="Comentário 1"
        )
        Comment.objects.create(
            mammal=self.mammal1,
            user=self.user2,
            content="Comentário 2"
        )
        
        # Buscar mamífero com contagem de comentários
        mammal = Mammal.objects.annotate(
            comment_count=Count('comments')
        ).get(pk=self.mammal1.pk)
        
        assert mammal.comment_count == 2
    
    def test_mammal_with_favorites_count(self):
        """Testa contagem de favoritos por mamífero"""
        # Adicionar favoritos
        Favorite.objects.create(user=self.user1, mammal=self.mammal1)
        Favorite.objects.create(user=self.user2, mammal=self.mammal1)
        
        # Buscar mamífero com contagem de favoritos
        mammal = Mammal.objects.annotate(
            favorite_count=Count('favorited_by')
        ).get(pk=self.mammal1.pk)
        
        assert mammal.favorite_count == 2
    
    def test_user_favorites_relationship(self):
        """Testa relacionamento de favoritos do usuário"""
        # Adicionar favoritos
        Favorite.objects.create(user=self.user1, mammal=self.mammal1)
        Favorite.objects.create(user=self.user1, mammal=self.mammal2)
        
        # Buscar favoritos do usuário
        user_favorites = self.user1.favorites.all()
        
        assert user_favorites.count() == 2
        favorited_mammals = [f.mammal for f in user_favorites]
        assert self.mammal1 in favorited_mammals
        assert self.mammal2 in favorited_mammals
    
    def test_mammal_ordering(self):
        """Testa ordenação de mamíferos"""
        # Mamíferos devem estar ordenados por common_name (definido no Meta)
        mammals = Mammal.objects.all()
        
        # Verificar ordem alfabética
        names = [m.common_name for m in mammals]
        assert names == sorted(names)
    
    def test_short_description_property(self):
        """Testa a propriedade short_description"""
        # Criar mamífero com descrição longa
        long_desc = "A" * 250
        mammal = Mammal.objects.create(
            common_name="Teste",
            binomial_name="Test test",
            description=long_desc
        )
        
        # Verificar que short_description trunca
        assert len(mammal.short_description) <= 203  # 200 + "..."
        assert mammal.short_description.endswith("...")
    
    def test_mammal_str_representation(self):
        """Testa a representação em string do mamífero"""
        mammal_str = str(self.mammal1)
        
        assert "Tigre-de-Java" in mammal_str
        assert "Panthera tigris sondaica" in mammal_str
    
    def test_comment_ordering(self):
        """Testa ordenação de comentários (mais recente primeiro)"""
        # Criar comentários
        comment1 = Comment.objects.create(
            mammal=self.mammal1,
            user=self.user1,
            content="Primeiro"
        )
        
        comment2 = Comment.objects.create(
            mammal=self.mammal1,
            user=self.user2,
            content="Segundo"
        )
        
        # Buscar comentários
        comments = Comment.objects.filter(mammal=self.mammal1)
        
        # O mais recente deve vir primeiro
        assert comments.first() == comment2
        assert comments.last() == comment1
    
    def test_unique_favorite_constraint(self):
        """Testa que não é possível criar favorito duplicado"""
        # Criar favorito
        Favorite.objects.create(user=self.user1, mammal=self.mammal1)
        
        # Tentar criar duplicado
        with pytest.raises(Exception):  # IntegrityError
            Favorite.objects.create(user=self.user1, mammal=self.mammal1)
    
    def test_cascade_delete_mammal(self):
        """Testa que deletar mamífero deleta comentários e favoritos"""
        # Criar comentário e favorito
        Comment.objects.create(
            mammal=self.mammal1,
            user=self.user1,
            content="Comentário"
        )
        Favorite.objects.create(user=self.user1, mammal=self.mammal1)
        
        mammal_id = self.mammal1.pk
        
        # Deletar mamífero
        self.mammal1.delete()
        
        # Verificar que comentários e favoritos foram deletados
        assert not Comment.objects.filter(mammal_id=mammal_id).exists()
        assert not Favorite.objects.filter(mammal_id=mammal_id).exists()
    
    def test_cascade_delete_user(self):
        """Testa que deletar usuário deleta comentários e favoritos"""
        # Criar comentário e favorito
        Comment.objects.create(
            mammal=self.mammal1,
            user=self.user1,
            content="Comentário"
        )
        Favorite.objects.create(user=self.user1, mammal=self.mammal1)
        
        user_id = self.user1.pk
        
        # Deletar usuário
        self.user1.delete()
        
        # Verificar que comentários e favoritos foram deletados
        assert not Comment.objects.filter(user_id=user_id).exists()
        assert not Favorite.objects.filter(user_id=user_id).exists()

