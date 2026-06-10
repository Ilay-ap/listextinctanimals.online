from django.apps import AppConfig


class MammalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mammals'
    
    def ready(self):
        """Executado quando o app está pronto"""
        # Importar apenas para registrar signals, se houver
        pass
