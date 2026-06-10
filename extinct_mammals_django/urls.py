"""
URL configuration for extinct_mammals_django project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),  # URL para mudança de idioma
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('mammals.urls')),
    path('accounts/', include('accounts.urls')),
)

# Servir arquivos estáticos e de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Handlers de erro personalizados
handler404 = 'mammals.views.custom_404'
handler500 = 'mammals.views.custom_500'
