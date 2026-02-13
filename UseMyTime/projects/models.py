from django.db import models
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

# Модель проектов
class Project(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='projects')
    title = models.CharField(max_length=200, verbose_name='Название проекта')
    description = models.TextField(verbose_name='Описание проекта')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_archived = models.BooleanField(default=False, verbose_name='В архиве')
    total_time = models.DurationField(default=timedelta(0), verbose_name='Общее время')
    review_status = models.CharField(
        max_length=20,
        choices=(
            ('none', 'Не на проверке'),
            ('in_review', 'На проверке'),
            ('approved', 'Принят'),
            ('rejected', 'Возвращен'),
        ),
        default='none',
        verbose_name='Статус проверки'
    )
    review_submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_projects_for_review',
        verbose_name='Кто отправил на проверку'
    )
    review_submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='Когда отправлен на проверку')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_projects',
        verbose_name='Проверил проект'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата проверки проекта')
    review_comment = models.TextField(blank=True, verbose_name='Комментарий проверки проекта')
    submit_comment = models.TextField(blank=True, verbose_name='Комментарий отправки на проверку')

    def get_hours_minutes_seconds(self):
        seconds = int(self.total_time.total_seconds())
        return [seconds // 3600, (seconds % 3600) // 60, seconds % 60]  # [hours, minutes, seconds]

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'

    def __str__(self):
        return self.title

# Модель активного проекта
# Для него и будет учитываться время
class ActiveProject(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='active_project')
    project = models.ForeignKey(Project, 
                                on_delete=models.CASCADE, 
                                null=True, blank=True)
    in_work = models.BooleanField(default=False, verbose_name='Запущен')
    last_started_at = models.DateTimeField(null=True, blank=True, verbose_name='Время запуска')

    class Meta:
        verbose_name = 'Активный проект'
        verbose_name_plural = 'Активные проекты'

# Таймеры по проектам (независимые, можно запускать несколько одновременно)
class ProjectTimer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_timers', verbose_name='Пользователь')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='timers', verbose_name='Проект')
    current_task = models.ForeignKey('Task', on_delete=models.SET_NULL, null=True, blank=True, related_name='running_timers', verbose_name='Текущая задача')
    in_work = models.BooleanField(default=False, verbose_name='Идёт отсчёт')
    last_started_at = models.DateTimeField(null=True, blank=True, verbose_name='Время запуска')

    def start(self, program=None):
        if self.in_work:
            return
        self.in_work = True
        self.last_started_at = timezone.now()
        self.save()

    def stop(self):
        if not self.in_work or not self.last_started_at:
            return timedelta(0)
        duration = timezone.now() - self.last_started_at
        self.in_work = False
        self.save()
        return duration

    class Meta:
        verbose_name = 'Таймер проекта'
        verbose_name_plural = 'Таймеры проектов'
        constraints = [
            models.UniqueConstraint(fields=['user', 'project'], name='uniq_user_project_timer')
        ]

# Модель подзадач проекта
class Task(models.Model):
    project = models.ForeignKey(Project, 
                                on_delete=models.CASCADE,
                                related_name='tasks',
                                verbose_name='Проект')
    text = models.TextField(verbose_name='Текст задачи')
    is_done = models.BooleanField(default=False, verbose_name='Выполнена')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата начала')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата завершения')
    status = models.CharField(
        max_length=20,
        choices=(
            ('new', 'Новая'),
            ('in_progress', 'В работе'),
            ('done', 'Готово'),
        ),
        default='new',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'

    def __str__(self):
        return self.text


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments', verbose_name='Задача')
    file = models.FileField(upload_to='task_attachments/%Y/%m/%d/', verbose_name='Файл')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')

    class Meta:
        verbose_name = 'Вложение задачи'
        verbose_name_plural = 'Вложения задач'


class TimeEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='time_entries', verbose_name='Пользователь')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='time_entries', verbose_name='Проект')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='time_entries', verbose_name='Задача')
    started_at = models.DateTimeField(verbose_name='Начало')
    ended_at = models.DateTimeField(verbose_name='Окончание')
    seconds = models.PositiveIntegerField(verbose_name='Секунды')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Запись времени'
        verbose_name_plural = 'Записи времени'


class ProjectAttachment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='attachments', verbose_name='Проект')
    file = models.FileField(upload_to='project_attachments/%Y/%m/%d/', verbose_name='Файл')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='project_attachments', verbose_name='Загрузил')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')

    class Meta:
        verbose_name = 'Вложение проекта'
        verbose_name_plural = 'Вложения проекта'