from django.contrib import admin
from .models import Mammal, Comment, Favorite, Rating


@admin.register(Mammal)
class MammalAdmin(admin.ModelAdmin):
    list_display = ['common_name', 'binomial_name', 'continent', 'taxonomy_order', 'created_at']
    list_filter = ['continent', 'taxonomy_order', 'created_at']
    search_fields = ['common_name', 'binomial_name', 'description']
    ordering = ['common_name']
    date_hierarchy = 'created_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'mammal', 'content_preview', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['content', 'user__username', 'mammal__common_name']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Conteúdo'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'mammal', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'mammal__common_name']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'mammal', 'score', 'stars_display', 'created_at', 'updated_at']
    list_filter = ['score', 'created_at', 'updated_at']
    search_fields = ['user__username', 'mammal__common_name', 'review']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def stars_display(self, obj):
        return obj.stars_display
    stars_display.short_description = 'Estrelas'
