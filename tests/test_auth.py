"""
Testes de Autenticação - test_auth.py

Testa o sistema de autenticação:
- Registro de novo usuário
- Login com credenciais corretas
- Login com senha errada
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from accounts.models import UserProfile


@pytest.mark.django_db
class TestAuthentication:
    """Classe de testes para autenticação de usuários"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()

        # Criar usuário de teste
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="senha123"
        )
        # UserProfile é criado automaticamente pelo signal, apenas atualizar
        profile, created = UserProfile.objects.get_or_create(user=self.test_user)
        profile.is_admin = False
        profile.save()

    def test_register_new_user_success(self):
        """
        Teste 1: Registro de novo usuário funciona
        Verifica se um novo usuário pode se registrar com sucesso
        """
        # Dados do novo usuário
        user_data = {
            "username": "novousuario",
            "email": "novo@example.com",
            "password": "senha123456",
            "password_confirm": "senha123456",
        }

        # Fazer requisição POST para registro
        response = self.client.post(
            reverse("accounts:register"), data=user_data, follow=True
        )

        # Verificar se foi criado
        assert response.status_code == 200
        assert User.objects.filter(username="novousuario").exists()

        # Verificar se o usuário foi criado corretamente
        new_user = User.objects.get(username="novousuario")
        assert new_user.email == "novo@example.com"
        assert new_user.check_password("senha123456")

        # Verificar se o perfil foi criado
        assert UserProfile.objects.filter(user=new_user).exists()

        # Verificar se foi feito login automático
        assert response.wsgi_request.user.is_authenticated
        assert response.wsgi_request.user.username == "novousuario"

    def test_login_with_correct_credentials(self):
        """
        Teste 2: Login com credenciais corretas funciona
        Verifica se um usuário pode fazer login com credenciais válidas
        """
        # Dados de login
        login_data = {"username": "testuser", "password": "senha123"}

        # Fazer requisição POST para login
        response = self.client.post(
            reverse("accounts:login"), data=login_data, follow=True
        )

        # Verificar se o login foi bem-sucedido
        assert response.status_code == 200
        assert response.wsgi_request.user.is_authenticated
        assert response.wsgi_request.user.username == "testuser"

        # Verificar se foi redirecionado para a página inicial
        assert response.redirect_chain[-1][0] == reverse("mammals:index")

    def test_login_with_wrong_password_fails(self):
        """
        Teste 3: Login com senha errada falha
        Verifica se o login falha com senha incorreta
        """
        # Dados de login com senha errada
        login_data = {"username": "testuser", "password": "senhaerrada"}

        # Fazer requisição POST para login
        response = self.client.post(reverse("accounts:login"), data=login_data)

        # Verificar se o login falhou
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated

        # Verificar se há mensagem de erro
        messages = list(response.context["messages"])
        assert len(messages) > 0
        assert "incorrect" in str(messages[0]).lower()


@pytest.mark.django_db
class TestAuthenticationEdgeCases:
    """Testes adicionais para casos extremos de autenticação"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()

    def test_register_with_duplicate_username(self):
        """Testa registro com username duplicado"""
        # Criar primeiro usuário
        User.objects.create_user(
            username="usuario1", email="user1@example.com", password="senha123"
        )

        # Tentar criar outro com mesmo username
        user_data = {
            "username": "usuario1",
            "email": "outro@example.com",
            "password": "senha123",
            "password_confirm": "senha123",
        }

        response = self.client.post(reverse("accounts:register"), data=user_data)

        # Verificar que falhou
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated

        # Verificar mensagem de erro
        messages = list(response.context["messages"])
        assert any("in use" in str(m).lower() for m in messages)

    def test_register_with_mismatched_passwords(self):
        """Testa registro com senhas que não coincidem"""
        user_data = {
            "username": "novousuario",
            "email": "novo@example.com",
            "password": "senha123",
            "password_confirm": "senha456",
        }

        response = self.client.post(reverse("accounts:register"), data=user_data)

        # Verificar que falhou
        assert response.status_code == 200
        assert not User.objects.filter(username="novousuario").exists()

        # Verificar mensagem de erro
        messages = list(response.context["messages"])
        assert any("do not match" in str(m).lower() for m in messages)

    def test_register_with_short_password(self):
        """Testa registro com senha muito curta"""
        user_data = {
            "username": "novousuario",
            "email": "novo@example.com",
            "password": "123",
            "password_confirm": "123",
        }

        response = self.client.post(reverse("accounts:register"), data=user_data)

        # Verificar que falhou
        assert response.status_code == 200
        assert not User.objects.filter(username="novousuario").exists()

        # Verificar mensagem de erro
        messages = list(response.context["messages"])
        assert any("at least 6" in str(m).lower() for m in messages)

    def test_login_with_nonexistent_user(self):
        """Testa login com usuário inexistente"""
        login_data = {"username": "usuarioinexistente", "password": "qualquersenha"}

        response = self.client.post(reverse("accounts:login"), data=login_data)

        # Verificar que falhou
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated

    def test_logout_redirects_to_index(self):
        """Testa se logout redireciona para a página inicial"""
        # Criar e fazer login de usuário
        user = User.objects.create_user(username="testuser", password="senha123")
        self.client.login(username="testuser", password="senha123")

        # Fazer logout
        response = self.client.get(reverse("accounts:logout"), follow=True)

        # Verificar redirecionamento
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated
        assert response.redirect_chain[-1][0] == reverse("mammals:index")

    def test_authenticated_user_cannot_access_register(self):
        """Testa se usuário autenticado não pode acessar página de registro"""
        # Criar e fazer login de usuário
        user = User.objects.create_user(username="testuser", password="senha123")
        self.client.login(username="testuser", password="senha123")

        # Tentar acessar página de registro
        response = self.client.get(reverse("accounts:register"), follow=True)

        # Deve redirecionar para index
        assert response.redirect_chain[-1][0] == reverse("mammals:index")

    def test_authenticated_user_cannot_access_login(self):
        """Testa se usuário autenticado não pode acessar página de login"""
        # Criar e fazer login de usuário
        user = User.objects.create_user(username="testuser", password="senha123")
        self.client.login(username="testuser", password="senha123")

        # Tentar acessar página de login
        response = self.client.get(reverse("accounts:login"), follow=True)

        # Deve redirecionar para index
        assert response.redirect_chain[-1][0] == reverse("mammals:index")
