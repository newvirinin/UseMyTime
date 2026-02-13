from django.contrib import admin
from .models import Question

# Добавление вопросов в админку
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['fio', 'position_display', 'user_email', 'is_closed', 'created_at']
    exclude = ('name', 'email')
    readonly_fields = ('created_at',)

    def fio(self, obj):
        if not obj.user:
            return ''
        user = obj.user
        patronymic = getattr(getattr(user, 'profile', None), 'surname', '') or ''
        parts = [user.last_name or '', user.first_name or '', patronymic]
        full = ' '.join(p.strip() for p in parts if p)
        return full if full else user.username
    fio.short_description = 'ФИО'

    def user_email(self, obj):
        return obj.user.email if obj.user else ''
    user_email.short_description = 'Email'

    def position_display(self, obj):
        if not obj.user:
            return ''
        profile = getattr(obj.user, 'profile', None)
        return getattr(profile, 'position', '') or ''
    position_display.short_description = 'Должность'