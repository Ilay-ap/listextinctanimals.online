from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extensão do modelo User para adicionar campo is_admin"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Usuário"
    )
    is_admin = models.BooleanField(
        default=False,
        verbose_name="É Administrador",
        help_text="Define se o usuário tem privilégios administrativos"
    )

    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"

    def __str__(self):
        return f"Perfil de {self.user.username}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Cria ou atualiza UserProfile automaticamente - CORRIGIDO para evitar duplicação"""
    # Usar get_or_create para evitar erro de duplicação
    UserProfile.objects.get_or_create(user=instance)
