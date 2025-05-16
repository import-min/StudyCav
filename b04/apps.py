from django.apps import AppConfig

class B04Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'b04'
    def ready(self):
        import b04.signals
