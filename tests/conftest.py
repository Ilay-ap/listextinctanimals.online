"""
Configurações e fixtures compartilhadas para todos os testes
"""
import pytest
from django.contrib.auth.models import User
from accounts.models import UserProfile


@pytest.fixture
def create_user(db):
    """Fixture para criar usuários de teste"""
    def make_user(username='testuser', password='testpass123', email='test@example.com', is_admin=False):
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.is_admin = is_admin
        profile.save()
        return user
    return make_user


@pytest.fixture
def regular_user(create_user):
    """Fixture para usuário regular"""
    return create_user(username='regular', password='pass123', is_admin=False)


@pytest.fixture
def admin_user(create_user):
    """Fixture para usuário administrador"""
    return create_user(username='admin', password='admin123', is_admin=True)


@pytest.fixture
def authenticated_client(client, regular_user):
    """Fixture para cliente autenticado como usuário regular"""
    client.login(username='regular', password='pass123')
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Fixture para cliente autenticado como administrador"""
    client.login(username='admin', password='admin123')
    return client
