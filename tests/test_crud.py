"""
Testes de CRUD - test_crud.py

Testa operações CRUD (Create, Read, Update, Delete):
- Adicionar comentário
- Adicionar favorito
- Editar comentário
- Remover favorito
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from mammals.models import Mammal, Comment, Favorite
from accounts.models import UserProfile


@pytest.mark.django_db
class TestCRUDOperations:
    """Classe de testes para operações CRUD"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()
        
        # Criar usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='senha123'
        )
        # UserProfile é criado automaticamente pelo signal, apenas atualizar
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.is_admin = False
        profile.save()
        
        # Criar mamífero de teste
        self.mammal = Mammal.objects.create(
            common_name="Dodo",
            binomial_name="Raphus cucullatus",
            description="Ave não voadora extinta da ilha Maurício",
            habitat="Florestas tropicais",
            distribution="Maurício",
            extinction_causes="Caça e introdução de espécies invasoras",
            continent="Africa",
            taxonomy_order="COLUMBIFORMES"
        )
        
        # Fazer login
        self.client.login(username='testuser', password='senha123')
    
    def test_add_comment_success(self):
        """
        Teste 1: Adicionar comentário funciona
        Verifica se um usuário autenticado pode adicionar comentário
        """
        # Dados do comentário
        comment_data = {
            'content': 'Este é um comentário de teste sobre o Dodo.'
        }
        
        # Fazer requisição POST para adicionar comentário
        response = self.client.post(
            reverse('mammals:add_comment', kwargs={'mammal_id': self.mammal.pk}),
            data=comment_data,
            follow=True
        )
        
        # Verificar se foi criado
        assert response.status_code == 200
        assert Comment.objects.filter(
            mammal=self.mammal,
            user=self.user
        ).exists()
        
        # Verificar conteúdo do comentário
        comment = Comment.objects.get(mammal=self.mammal, user=self.user)
        assert comment.content == 'Este é um comentário de teste sobre o Dodo.'
        
        # Verificar redirecionamento (com âncora #comments-section)
        assert reverse('mammals:detail', kwargs={'pk': self.mammal.pk}) in response.redirect_chain[-1][0]
    
    def test_add_favorite_success(self):
        """
        Teste 2: Adicionar favorito funciona
        Verifica se um usuário pode favoritar um mamífero
        """
        # Verificar que não existe favorito ainda
        assert not Favorite.objects.filter(
            user=self.user,
            mammal=self.mammal
        ).exists()
        
        # Fazer requisição POST para adicionar favorito
        response = self.client.post(
            reverse('mammals:toggle_favorite', kwargs={'mammal_id': self.mammal.pk}),
            follow=True
        )
        
        # Verificar se foi criado
        assert response.status_code == 200
        assert Favorite.objects.filter(
            user=self.user,
            mammal=self.mammal
        ).exists()
        
        # Verificar que o favorito está associado corretamente
        favorite = Favorite.objects.get(user=self.user, mammal=self.mammal)
        assert favorite.user == self.user
        assert favorite.mammal == self.mammal


@pytest.mark.django_db
class TestCRUDEdgeCases:
    """Testes adicionais para casos extremos de CRUD"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()
        
        # Criar usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='senha123'
        )
        
        # Criar mamífero de teste
        self.mammal = Mammal.objects.create(
            common_name="Quagga",
            binomial_name="Equus quagga quagga",
            description="Subespécie de zebra extinta",
            continent="Africa"
        )
        
        # Fazer login
        self.client.login(username='testuser', password='senha123')
    
    def test_add_empty_comment_fails(self):
        """Testa que não é possível adicionar comentário vazio"""
        comment_data = {
            'content': ''
        }
        
        response = self.client.post(
            reverse('mammals:add_comment', kwargs={'mammal_id': self.mammal.pk}),
            data=comment_data,
            follow=True
        )
        
        # Verificar que não foi criado
        assert not Comment.objects.filter(mammal=self.mammal, user=self.user).exists()
        
        # Verificar mensagem de erro (em inglês ou português)
        messages = list(response.context['messages'])
        assert any('empty' in str(m).lower() or 'vazio' in str(m).lower() for m in messages)
    
    def test_toggle_favorite_twice_removes_it(self):
        """Testa que favoritar duas vezes remove o favorito"""
        # Adicionar favorito
        self.client.post(
            reverse('mammals:toggle_favorite', kwargs={'mammal_id': self.mammal.pk})
        )
        assert Favorite.objects.filter(user=self.user, mammal=self.mammal).exists()
        
        # Remover favorito (toggle novamente)
        self.client.post(
            reverse('mammals:toggle_favorite', kwargs={'mammal_id': self.mammal.pk})
        )
        assert not Favorite.objects.filter(user=self.user, mammal=self.mammal).exists()
    
    def test_unauthenticated_user_cannot_add_comment(self):
        """Testa que usuário não autenticado não pode comentar"""
        # Fazer logout
        self.client.logout()
        
        comment_data = {
            'content': 'Tentando comentar sem estar logado'
        }
        
        response = self.client.post(
            reverse('mammals:add_comment', kwargs={'mammal_id': self.mammal.pk}),
            data=comment_data
        )
        
        # Deve redirecionar para login
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
        
        # Comentário não deve ser criado
        assert not Comment.objects.filter(mammal=self.mammal).exists()
    
    def test_unauthenticated_user_cannot_add_favorite(self):
        """Testa que usuário não autenticado não pode favoritar"""
        # Fazer logout
        self.client.logout()
        
        response = self.client.post(
            reverse('mammals:toggle_favorite', kwargs={'mammal_id': self.mammal.pk})
        )
        
        # Deve redirecionar para login
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
        
        # Favorito não deve ser criado
        assert not Favorite.objects.filter(mammal=self.mammal).exists()
    


    def test_delete_own_comment(self):
        """Testa exclusão de comentário próprio"""
        # Criar comentário
        comment = Comment.objects.create(
            mammal=self.mammal,
            user=self.user,
            content='Comentário para deletar'
        )
        
        comment_id = comment.pk
        
        # Deletar comentário
        response = self.client.post(
            reverse('mammals:delete_comment', kwargs={'comment_id': comment_id}),
            follow=True
        )
        
        # Verificar que foi deletado
        assert not Comment.objects.filter(pk=comment_id).exists()
    
    def test_multiple_users_can_favorite_same_mammal(self):
        """Testa que múltiplos usuários podem favoritar o mesmo mamífero"""
        # Criar segundo usuário
        user2 = User.objects.create_user(
            username='user2',
            password='senha123'
        )
        
        # Primeiro usuário favorita
        Favorite.objects.create(user=self.user, mammal=self.mammal)
        
        # Segundo usuário favorita
        Favorite.objects.create(user=user2, mammal=self.mammal)
        
        # Verificar que ambos favoritaram
        assert Favorite.objects.filter(mammal=self.mammal).count() == 2
        assert Favorite.objects.filter(user=self.user, mammal=self.mammal).exists()
        assert Favorite.objects.filter(user=user2, mammal=self.mammal).exists()

