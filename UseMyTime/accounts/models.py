from django.db import models
from django.conf import settings
from django.contrib.auth.models import User as DjangoUser, Group as DjangoGroup

# Роли
ROLE_CHOICES = (
    ('employee', 'Сотрудник'),
    ('manager', 'Начальник отдела'),
    ('sector_manager', 'Начальник сектора'),
    ('director', 'Генеральный директор'),
)

class Department(models.Model):
    name = models.CharField('Название отдела', max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'

# Изменен порядок полей и добавлены новые
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE)
    surname = models.CharField(max_length=50, blank=True, verbose_name='Отчество', default='')
    position = models.CharField("Должность", max_length=100, blank=True)
    phone_internal = models.CharField("Внутренний номер", max_length=10, blank=True, default='')
    photo = models.ImageField(upload_to='users/%Y/%m/%d/',
                              blank=True,
                              verbose_name='Фото')
    role = models.CharField("Роль", max_length=20, choices=ROLE_CHOICES, default='employee')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Отдел')
    # Добавлено поле для связи: кто начальник у этого сотрудника
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True,  null=True, related_name='subordinates',
                                verbose_name="Начальник")
    def __str__(self):
        return f'Profile of {self.user.username}'
    
    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

# Прокси-модель Пользователь для отображения в разделе 'Профили'
class UserProxy(DjangoUser):
    class Meta:
        proxy = True
        app_label = 'accounts'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Профили'

# Прокси-модель Группа как 'Отделы' для переноса в раздел 'Профили'
class GroupProxy(DjangoGroup):
    class Meta:
        proxy = True
        app_label = 'accounts'
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'