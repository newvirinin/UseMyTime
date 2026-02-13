from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Профили'
    
    def ready(self):
        from django.db.models.signals import post_save
        from django.contrib.auth.models import User
        from .models import Profile
        
        def create_user_profile(sender, instance, created, **kwargs):
            if kwargs.get('raw'):
                return
            if created:
                Profile.objects.get_or_create(user=instance)
        
        post_save.connect(create_user_profile, sender=User)
