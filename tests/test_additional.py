"""
Testes Adicionais - test_additional.py

Testes extras para aumentar a cobertura de código:
- Testes de views adicionais
- Testes de models
- Testes de decorators
- Testes de URLs
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from mammals.models import Mammal, Comment, Favorite
from accounts.models import UserProfile


@pytest.mark.django_db
class TestFavoritesView:
    """Testes para a view de favoritos"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()
        
        # Criar usuário
        self.user = User.objects.create_user(
            username='testuser',
            password='senha123'
        )
        
        # Criar mamíferos
        self.mammal1 = Mammal.objects.create(
            common_name="Mamífero 1",
            binomial_name="Species one"
        )
        
        self.mammal2 = Mammal.objects.create(
            common_name="Mamífero 2",
            binomial_name="Species two"
        )
        
        # Fazer login
        self.client.login(username='testuser', password='senha123')
    
    def test_favorites_page_requires_login(self):
        """Testa que página de favoritos requer login"""
        # Fazer logout
        self.client.logout()
        
        response = self.client.get(reverse('mammals:favorites'))
        
        # Deve redirecionar para login
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
    
    def test_favorites_page_shows_user_favorites(self):
        """Testa que página de favoritos mostra favoritos do usuário"""
        # Adicionar favoritos
        Favorite.objects.create(user=self.user, mammal=self.mammal1)
        Favorite.objects.create(user=self.user, mammal=self.mammal2)
        
        response = self.client.get(reverse('mammals:favorites'))
        
        assert response.status_code == 200
        assert 'favorites' in response.context
        assert len(response.context['favorites']) == 2
    
    def test_favorites_page_empty_when_no_favorites(self):
        """Testa que página de favoritos está vazia quando não há favoritos"""
        response = self.client.get(reverse('mammals:favorites'))
        
        assert response.status_code == 200
        assert len(response.context['favorites']) == 0


@pytest.mark.django_db
class TestProfileViews:
    """Testes para views de perfil"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()
        
        # Criar usuário
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='senha123'
        )
        # UserProfile é criado automaticamente pelo signal, apenas atualizar
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.is_admin = False
        profile.save()
        
        # Fazer login
        self.client.login(username='testuser', password='senha123')
    
    def test_profile_page_requires_login(self):
        """Testa que página de perfil requer login"""
        self.client.logout()
        
        response = self.client.get(reverse('accounts:profile'))
        
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
    
    def test_profile_page_shows_user_info(self):
        """Testa que página de perfil mostra informações do usuário"""
        response = self.client.get(reverse('accounts:profile'))
        
        assert response.status_code == 200
        assert 'user_profile' in response.context
        assert response.context['user_profile'].user == self.user
    
    def test_edit_profile_page_requires_login(self):
        """Testa que página de edição de perfil requer login"""
        self.client.logout()
        
        response = self.client.get(reverse('accounts:edit_profile'))
        
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


@pytest.mark.django_db
class TestMammalDetailView:
    """Testes adicionais para view de detalhes"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()
        
        # Criar mamífero
        self.mammal = Mammal.objects.create(
            common_name="Dodo",
            binomial_name="Raphus cucullatus",
            description="Ave extinta"
        )
        
        # Criar usuário
        self.user = User.objects.create_user(
            username='testuser',
            password='senha123'
        )
    
    def test_detail_page_shows_comments(self):
        """Testa que página de detalhes mostra comentários"""
        # Criar comentários
        Comment.objects.create(
            mammal=self.mammal,
            user=self.user,
            content="Comentário 1"
        )
        Comment.objects.create(
            mammal=self.mammal,
            user=self.user,
            content="Comentário 2"
        )
        
        response = self.client.get(
            reverse('mammals:detail', kwargs={'pk': self.mammal.pk})
        )
        
        assert response.status_code == 200
        assert 'comments' in response.context
        assert response.context['comments'].count() == 2
    
    def test_detail_page_shows_favorite_status_when_logged_in(self):
        """Testa que página mostra status de favorito quando logado"""
        self.client.login(username='testuser', password='senha123')
        
        # Favoritar
        Favorite.objects.create(user=self.user, mammal=self.mammal)
        
        response = self.client.get(
            reverse('mammals:detail', kwargs={'pk': self.mammal.pk})
        )
        
        assert response.status_code == 200
        assert response.context['is_favorite'] is True
    
    def test_detail_page_favorite_false_when_not_favorited(self):
        """Testa que is_favorite é False quando não favoritado"""
        self.client.login(username='testuser', password='senha123')
        
        response = self.client.get(
            reverse('mammals:detail', kwargs={'pk': self.mammal.pk})
        )
        
        assert response.status_code == 200
        assert response.context['is_favorite'] is False
    
    def test_detail_page_favorite_false_when_not_logged_in(self):
        """Testa que is_favorite é False quando não logado"""
        response = self.client.get(
            reverse('mammals:detail', kwargs={'pk': self.mammal.pk})
        )
        
        assert response.status_code == 200
        assert response.context['is_favorite'] is False


@pytest.mark.django_db
class TestIndexView:
    """Testes adicionais para a página inicial"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()
        
        # Criar mamíferos
        for i in range(5):
            Mammal.objects.create(
                common_name=f"Mamífero {i}",
                binomial_name=f"Species {i}"
            )
        
        # Criar usuário
        self.user = User.objects.create_user(
            username='testuser',
            password='senha123'
        )
    
    def test_index_shows_all_mammals(self):
        """Testa que index mostra todos os mamíferos"""
        response = self.client.get(reverse('mammals:index'))
        
        assert response.status_code == 200
        # Com paginação, mammals é um objeto Page
        assert len(response.context['mammals']) == 5
    
    def test_index_shows_favorites_when_logged_in(self):
        """Testa que index mostra favoritos quando logado"""
        self.client.login(username='testuser', password='senha123')
        
        # Favoritar alguns mamíferos
        mammal1 = Mammal.objects.first()
        mammal2 = Mammal.objects.last()
        Favorite.objects.create(user=self.user, mammal=mammal1)
        Favorite.objects.create(user=self.user, mammal=mammal2)
        
        response = self.client.get(reverse('mammals:index'))
        
        assert response.status_code == 200
        assert 'favorites' in response.context
        assert len(response.context['favorites']) == 2
    
    def test_index_favorites_empty_when_not_logged_in(self):
        """Testa que favorites está vazio quando não logado"""
        response = self.client.get(reverse('mammals:index'))
        
        assert response.status_code == 200
        assert response.context['favorites'] == []


@pytest.mark.django_db
class TestModelMethods:
    """Testes para métodos dos models"""
    
    def test_mammal_get_absolute_url(self):
        """Testa o método get_absolute_url do Mammal"""
        mammal = Mammal.objects.create(
            common_name="Teste",
            binomial_name="Test test"
        )
        
        url = mammal.get_absolute_url()
        expected_url = reverse('mammals:detail', kwargs={'pk': mammal.pk})
        
        assert url == expected_url
    
    def test_mammal_short_description_with_short_text(self):
        """Testa short_description com texto curto"""
        mammal = Mammal.objects.create(
            common_name="Teste",
            binomial_name="Test test",
            description="Descrição curta"
        )
        
        assert mammal.short_description == "Descrição curta"
        assert not mammal.short_description.endswith("...")
    
    def test_comment_str_representation(self):
        """Testa a representação em string do Comment"""
        user = User.objects.create_user(username='testuser')
        mammal = Mammal.objects.create(
            common_name="Dodo",
            binomial_name="Raphus cucullatus"
        )
        comment = Comment.objects.create(
            mammal=mammal,
            user=user,
            content="Comentário teste"
        )
        
        comment_str = str(comment)
        assert "testuser" in comment_str
        assert "Dodo" in comment_str
    
    def test_favorite_str_representation(self):
        """Testa a representação em string do Favorite"""
        user = User.objects.create_user(username='testuser')
        mammal = Mammal.objects.create(
            common_name="Dodo",
            binomial_name="Raphus cucullatus"
        )
        favorite = Favorite.objects.create(
            user=user,
            mammal=mammal
        )
        
        favorite_str = str(favorite)
        assert "testuser" in favorite_str
        assert "Dodo" in favorite_str
    
    def test_user_profile_str_representation(self):
        """Testa a representação em string do UserProfile"""
        user = User.objects.create_user(username='testuser')
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.is_admin = False
        profile.save()
        
        profile_str = str(profile)
        assert "testuser" in profile_str


@pytest.mark.django_db
class TestSearchEndpoint:
    """Testes adicionais para o endpoint de busca"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()
        
        # Criar mamíferos diversos
        Mammal.objects.create(
            common_name="Tigre-da-Tasmânia",
            binomial_name="Thylacinus cynocephalus",
            description="Carnívoro marsupial",
            continent="Oceania",
            taxonomy_order="DASYUROMORPHIA"
        )
        
        Mammal.objects.create(
            common_name="Dodo",
            binomial_name="Raphus cucullatus",
            description="Ave não voadora",
            continent="Africa",
            taxonomy_order="COLUMBIFORMES"
        )
    
    def test_search_with_empty_query(self):
        """Testa busca com query vazia"""
        response = self.client.get(reverse('mammals:search'))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Retorna todos
    
    def test_search_by_description(self):
        """Testa busca por descrição"""
        response = self.client.get(
            reverse('mammals:search'),
            {'q': 'marsupial'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['common_name'] == "Tigre-da-Tasmânia"
    
    def test_search_returns_image_filename(self):
        """Testa que busca retorna image_filename"""
        response = self.client.get(reverse('mammals:search'))
        
        assert response.status_code == 200
        data = response.json()
        assert 'image_filename' in data[0]

