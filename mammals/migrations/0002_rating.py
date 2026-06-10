# Generated migration for Rating model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mammals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(choices=[(1, '1 estrela'), (2, '2 estrelas'), (3, '3 estrelas'), (4, '4 estrelas'), (5, '5 estrelas')], help_text='Avaliação de 1 a 5 estrelas', verbose_name='Pontuação')),
                ('review', models.TextField(blank=True, help_text='Comentário opcional sobre a avaliação', null=True, verbose_name='Comentário da Avaliação')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('mammal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='mammals.mammal', verbose_name='Mamífero')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Avaliação',
                'verbose_name_plural': 'Avaliações',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['user'], name='mammals_rat_user_id_idx'),
                    models.Index(fields=['mammal'], name='mammals_rat_mammal_id_idx'),
                    models.Index(fields=['score'], name='mammals_rat_score_idx'),
                ],
            },
        ),
        migrations.AlterUniqueTogether(
            name='rating',
            unique_together={('user', 'mammal')},
        ),
    ]
