from django.db import models
from django.conf import settings
    
# Модель для вопросов разработчикам
class Question(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    name = models.CharField(max_length=600, verbose_name='Имя')
    email = models.EmailField(verbose_name='Email')
    body = models.TextField(verbose_name='Текст сообщения')
    is_closed = models.BooleanField(verbose_name='Закрыт', default=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def save(self, *args, **kwargs):
        if self.user_id:
            full_name = self.user.get_full_name().strip()
            self.name = full_name if full_name else self.user.username
            self.email = self.user.email
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'