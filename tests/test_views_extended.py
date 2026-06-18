"""
Testes Estendidos de Views - test_views_extended.py

Testes adicionais para aumentar cobertura de código nas views
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from accounts.models import UserProfile
from mammals.models import Comment, Favorite, Mammal


@pytest.mark.django_db
class TestToggleFavorite:
    """Testes para a funcionalidade de toggle favorite"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()

        # Criar usuário
        self.user = User.objects.create_user(username="testuser", password="senha123")

        # Criar mamífero
        self.mammal = Mammal.objects.create(
            common_name="Dodo", binomial_name="Raphus cucullatus"
        )

        # Fazer login
        self.client.login(username="testuser", password="senha123")

    def test_toggle_favorite_adds_when_not_exists(self):
        """Testa que toggle adiciona favorito quando não existe"""
        response = self.client.post(
            reverse("mammals:toggle_favorite", kwargs={"mammal_id": self.mammal.pk}),
            follow=True,
        )

        assert response.status_code == 200
        assert Favorite.objects.filter(user=self.user, mammal=self.mammal).exists()

    def test_toggle_favorite_removes_when_exists(self):
        """Testa que toggle remove favorito quando já existe"""
        # Criar favorito
        Favorite.objects.create(user=self.user, mammal=self.mammal)

        response = self.client.post(
            reverse("mammals:toggle_favorite", kwargs={"mammal_id": self.mammal.pk}),
            follow=True,
        )

        assert response.status_code == 200
        assert not Favorite.objects.filter(user=self.user, mammal=self.mammal).exists()

    def test_toggle_favorite_redirects_to_referrer(self):
        """Testa que toggle redireciona para a página de origem"""
        response = self.client.post(
            reverse("mammals:toggle_favorite", kwargs={"mammal_id": self.mammal.pk}),
            HTTP_REFERER=reverse("mammals:detail", kwargs={"pk": self.mammal.pk}),
            follow=True,
        )

        assert response.status_code == 200


@pytest.mark.django_db
class TestEditProfile:
    """Testes para edição de perfil"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()

        # Criar usuário
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="senha123"
        )
        # UserProfile é criado automaticamente pelo signal, apenas atualizar
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.is_admin = False
        profile.save()

        # Fazer login
        self.client.login(username="testuser", password="senha123")

    def test_edit_profile_get_shows_form(self):
        """Testa que GET mostra formulário de edição"""
        response = response = self.client.get(reverse("accounts:edit_profile"))

        assert response.status_code == 200
        assert "accounts/edit_profile.html" in [t.name for t in response.templates]

    def test_edit_profile_update_username(self):
        """Testa atualização de username"""
        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "username": "newusername",
                "email": "test@example.com",
                "current_password": "",
                "new_password": "",
                "new_password_confirm": "",
            },
            follow=True,
        )

        self.user.refresh_from_db()
        assert self.user.username == "newusername"

    def test_edit_profile_update_email(self):
        """Testa atualização de email"""
        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "username": "testuser",
                "email": "newemail@example.com",
                "current_password": "",
                "new_password": "",
                "new_password_confirm": "",
            },
            follow=True,
        )

        self.user.refresh_from_db()
        assert self.user.email == "newemail@example.com"

    def test_edit_profile_change_password(self):
        """Testa mudança de senha"""
        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "current_password": "senha123",
                "new_password": "novasenha123",
                "new_password_confirm": "novasenha123",
            },
            follow=True,
        )

        self.user.refresh_from_db()
        assert self.user.check_password("novasenha123")

    def test_edit_profile_wrong_current_password(self):
        """Testa que senha atual errada falha"""
        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "current_password": "senhaerrada",
                "new_password": "novasenha123",
                "new_password_confirm": "novasenha123",
            },
        )

        assert response.status_code == 200
        messages = list(response.context["messages"])
        assert any("incorrect" in str(m).lower() for m in messages)

    def test_edit_profile_password_mismatch(self):
        """Testa que senhas diferentes falham"""
        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "current_password": "senha123",
                "new_password": "senha1",
                "new_password_confirm": "senha2",
            },
        )

        assert response.status_code == 200
        messages = list(response.context["messages"])
        assert any("do not match" in str(m).lower() for m in messages)

    def test_edit_profile_short_password(self):
        """Testa que senha curta falha"""
        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "current_password": "senha123",
                "new_password": "123",
                "new_password_confirm": "123",
            },
        )

        assert response.status_code == 200
        messages = list(response.context["messages"])
        assert any("at least 6" in str(m).lower() for m in messages)

    def test_edit_profile_duplicate_username(self):
        """Testa que username duplicado falha"""
        # Criar outro usuário
        User.objects.create_user(username="otheruser", password="senha123")

        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "username": "otheruser",
                "email": "test@example.com",
                "current_password": "",
                "new_password": "",
                "new_password_confirm": "",
            },
        )

        assert response.status_code == 200
        messages = list(response.context["messages"])
        assert any("in use" in str(m).lower() for m in messages)

    def test_edit_profile_duplicate_email(self):
        """Testa que email duplicado falha"""
        # Criar outro usuário
        User.objects.create_user(
            username="otheruser", email="other@example.com", password="senha123"
        )

        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "username": "testuser",
                "email": "other@example.com",
                "current_password": "",
                "new_password": "",
                "new_password_confirm": "",
            },
        )

        assert response.status_code == 200
        messages = list(response.context["messages"])
        assert any("registered" in str(m).lower() for m in messages)

    def test_edit_profile_new_password_without_current(self):
        """Testa que nova senha sem senha atual falha"""
        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "current_password": "",
                "new_password": "novasenha123",
                "new_password_confirm": "novasenha123",
            },
        )

        assert response.status_code == 200
        messages = list(response.context["messages"])
        assert any("current password" in str(m).lower() for m in messages)


@pytest.mark.django_db
class TestLoginRememberMe:
    """Testes para funcionalidade de lembrar login"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()

        # Criar usuário
        self.user = User.objects.create_user(username="testuser", password="senha123")

    def test_login_without_remember_expires_on_close(self):
        """Testa que login sem remember expira ao fechar navegador"""
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "testuser",
                "password": "senha123",
                # remember não enviado = False
            },
        )

        # Verificar que login foi bem-sucedido
        assert response.wsgi_request.user.is_authenticated

    def test_login_with_empty_fields(self):
        """Testa login com campos vazios"""
        response = self.client.post(
            reverse("accounts:login"), {"username": "", "password": ""}
        )

        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated
        messages = list(response.context["messages"])
        assert any("fill in all" in str(m).lower() for m in messages)


@pytest.mark.django_db
class TestRegisterValidations:
    """Testes adicionais para validações de registro"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()

    def test_register_with_empty_fields(self):
        """Testa registro com campos vazios"""
        response = self.client.post(
            reverse("accounts:register"),
            {"username": "", "email": "", "password": "", "password_confirm": ""},
        )

        assert response.status_code == 200
        assert not User.objects.filter(username="").exists()
        messages = list(response.context["messages"])
        assert any("fill in all" in str(m).lower() for m in messages)


@pytest.mark.django_db
class TestCommentOperations:
    """Testes adicionais para operações com comentários"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup executado antes de cada teste"""
        self.client = Client()

        # Criar usuário
        self.user = User.objects.create_user(username="testuser", password="senha123")

        # Criar mamífero
        self.mammal = Mammal.objects.create(
            common_name="Dodo", binomial_name="Raphus cucullatus"
        )

        # Fazer login
        self.client.login(username="testuser", password="senha123")

    def test_delete_comment_redirects_to_mammal_detail(self):
        """Testa que deletar comentário redireciona para detalhes do mamífero"""
        # Criar comentário
        comment = Comment.objects.create(
            mammal=self.mammal, user=self.user, content="Comentário para deletar"
        )

        response = self.client.post(
            reverse("mammals:delete_comment", kwargs={"comment_id": comment.pk}),
            follow=True,
        )

        assert response.status_code == 200
        # Verificar redirecionamento (com âncora #comments-section)
        assert (
            reverse("mammals:detail", kwargs={"pk": self.mammal.pk})
            in response.redirect_chain[-1][0]
        )

    def test_cannot_delete_others_comment(self):
        """Testa que não é possível deletar comentário de outro usuário"""
        # Criar outro usuário
        other_user = User.objects.create_user(username="otheruser", password="senha123")

        # Criar comentário do outro usuário
        comment = Comment.objects.create(
            mammal=self.mammal, user=other_user, content="Comentário do outro usuário"
        )

        comment_id = comment.pk

        # Tentar deletar
        response = self.client.post(
            reverse("mammals:delete_comment", kwargs={"comment_id": comment_id}),
            follow=True,
        )

        # Comentário não deve ser deletado
        assert Comment.objects.filter(pk=comment_id).exists()
