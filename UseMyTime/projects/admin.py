from django.contrib import admin
from .models import Task, Project, TaskAttachment, ProjectAttachment

# Настройка отображения Проектов
class ProjectAttachmentInline(admin.TabularInline):
    model = ProjectAttachment
    extra = 0
    fields = ('file', 'uploaded_by', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'is_archived', 'created_at']
    list_display_links = ['id', 'title']
    search_fields = ['title', 'user__username', 'user__last_name', 'user__first_name']
    list_filter = ['is_archived', 'created_at']
    inlines = [ProjectAttachmentInline]


class TaskAttachmentInline(admin.TabularInline):
    model = TaskAttachment
    extra = 0
    fields = ('file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


# Настройка отображения Задач
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    def creator(self, obj):
        return obj.project.user
    creator.short_description = 'Создатель'

    list_display = ['id', 'text', 'project', 'creator', 'status', 'is_done', 'created_at']
    list_display_links = ['id', 'text']
    search_fields = ['text', 'project__title', 'project__user__username']
    list_filter = ['status', 'is_done', 'created_at']
    inlines = [TaskAttachmentInline]
    fields = ('project', 'text', 'status', 'is_done', 'created_at')
    readonly_fields = ('created_at',)

    actions = ['approve_done', 'reject_to_in_progress']

    def approve_done(self, request, queryset):
        updated = queryset.update(status='done', is_done=True)
        self.message_user(request, f'Подтверждено как Готово: {updated}')
    approve_done.short_description = 'Подтвердить как Готово'

    def reject_to_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress', is_done=False)
        self.message_user(request, f'Возвращено в работу: {updated}')
    reject_to_in_progress.short_description = 'Вернуть в работу'
