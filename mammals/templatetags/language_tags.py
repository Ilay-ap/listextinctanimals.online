from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def get_available_languages():
    """Retorna a lista de idiomas disponíveis"""
    return settings.LANGUAGES

@register.simple_tag(takes_context=True)
def get_current_language(context):
    """Retorna o idioma atual"""
    request = context.get('request')
    if request:
        return request.LANGUAGE_CODE
    return settings.LANGUAGE_CODE

