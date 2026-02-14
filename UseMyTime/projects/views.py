from django.shortcuts import render, HttpResponse, HttpResponseRedirect, get_object_or_404
from django.http import FileResponse
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from django.urls import reverse_lazy
from django.views.generic import UpdateView, CreateView, DeleteView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from .models import Project, ActiveProject, Task, ProjectTimer, TimeEntry, TaskAttachment, ProjectAttachment

# Создание проекта
class ProjectCreateView(LoginRequiredMixin, CreateView):
    template_name = 'projects/create_update.html'
    model = Project
    fields = ['title', 'description']
    def form_valid(self, form):
        form.instance.user = self.request.user
        project = form.save()
        tasks_texts = [t.strip() for t in self.request.POST.getlist('tasks') if t.strip()]
        for text in tasks_texts:
            Task.objects.create(project=project, text=text)
        return super().form_valid(form)
    def get_success_url(self):
        return reverse_lazy('project_detail', kwargs={'pk': self.object.pk})
    
# Обновление проекта
class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'projects/create_update.html'
    model = Project
    fields = ['title', 'description']
    def get_success_url(self):
        return reverse_lazy('project_detail', kwargs={'pk': self.object.pk})
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
    def form_valid(self, form):
        project = form.save()
        tasks_texts = [t.strip() for t in self.request.POST.getlist('tasks') if t.strip()]
        for task in project.tasks.all():
            if task.text not in tasks_texts:
                task.delete()
        existing_texts = [task.text for task in project.tasks.all()]
        for text in tasks_texts:
            if text not in existing_texts:
                Task.objects.create(project=project, text=text)
        return super().form_valid(form)

# Удаление проекта
class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('project_create')
    template_name = 'projects/delete_confirm.html'
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

# Получение архива проектов
class ProjectListView(LoginRequiredMixin, ListView):
    template_name = 'projects/list.html'
    model = Project
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user).filter(is_archived=False)

class ArchiveProjectListView(LoginRequiredMixin, ListView):
    template_name = 'projects/archive.html'
    model = Project
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user).filter(is_archived=True)

# Просмотр задач пользователя
class MyTasksView(LoginRequiredMixin, ListView):
    template_name = 'workflow/my_tasks.html'
    model = Task
    context_object_name = 'object_list'
    
    def get_queryset(self):
        return Task.objects.filter(project__user=self.request.user).order_by('-created_at')

# Получение конкретного проекта
class ProjectDetailView(LoginRequiredMixin, DetailView):
    template_name = 'projects/detail.html'
    model = Project
    def get_queryset(self):
        qs = super().get_queryset()
        # Расширяем доступ для руководителей
        role = getattr(getattr(self.request.user, 'profile', None), 'role', None)
        if role == 'director':
            return qs
        if role in ['manager', 'sector_manager']:
            try:
                from accounts.models import Profile
                my_profile = self.request.user.profile
                subs = Profile.objects.filter(manager=my_profile).values_list('user_id', flat=True)
                return qs.filter(Q(user=self.request.user) | Q(user_id__in=list(subs)))
            except Exception:
                return qs.filter(user=self.request.user)
        # Сотрудник видит только свои проекты
        return qs.filter(user=self.request.user)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        timer = ProjectTimer.objects.filter(user=self.request.user, project=project).first()
        context['project_timer'] = timer
        if timer and timer.last_started_at:
            context['timer_started_at_epoch'] = int(timer.last_started_at.timestamp())
        else:
            context['timer_started_at_epoch'] = None
        context['timer_in_work'] = bool(timer and timer.in_work)
        # base total seconds of project from DB (without currently running increment)
        context['project_total_seconds'] = int(project.total_time.total_seconds())
        # precompute flags for template logic
        tasks_incomplete = project.tasks.filter(status__in=['new', 'in_progress']).exists()
        context['all_tasks_done'] = not tasks_incomplete
        # Разрешаем отправку только если все задачи завершены и проект не принят и не в проверке
        context['can_submit_review'] = (not tasks_incomplete) and (project.review_status in ['none', 'rejected'])
        return context

# Активация проекта
@require_POST
@login_required
def project_activate(request):
    active_project, _ = ActiveProject.objects.get_or_create(user=request.user)
    project_id = request.POST.get('project_id')
    try:
        project = Project.objects.get(id=project_id, user=request.user)
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Проект не найден'})
    # Запрет активации, если проект на проверке или уже принят
    if project.review_status in ['in_review', 'approved']:
        messages.error(request, 'Нельзя активировать проект: он на проверке или уже принят')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': project_id}))
    active_project.project = project
    active_project.save()
    
    # Также создаем ProjectTimer для нового механизма
    timer, _ = ProjectTimer.objects.get_or_create(user=request.user, project=project)
    
    return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': project_id}))

# Запуска активного проекта
@require_POST
@login_required
def project_start(request):
    active_project = ActiveProject.objects.filter(user=request.user).first()
    if not active_project:
        return JsonResponse({'is_success': False, 
                             'error': 'Нет активного проекта'})
    if active_project.in_work:
        return JsonResponse({'is_success': False, 
                             'error': 'Проект уже запущен'})
    active_project.in_work = True
    active_project.last_started_at = timezone.now()
    active_project.save()
    return JsonResponse({'is_success': True})

# Остановка активного проекта
@require_POST
@login_required
def project_stop(request):
    active_project = ActiveProject.objects.filter(user=request.user).first()
    if not active_project or not active_project.project:
        return JsonResponse({'is_success': False, 
                             'error': 'Нет активного проекта'})
    if not active_project.in_work:
        return JsonResponse({'is_success': False, 
                             'error': 'Проект уже остановлен'})
    started_at = active_project.last_started_at
    now = timezone.now()
    duration = now - started_at
    active_project.in_work = False
    active_project.project.total_time += duration
    active_project.save()
    active_project.project.save()
    TimeEntry.objects.create(
        user=request.user,
        project=active_project.project,
        started_at=started_at,
        ended_at=now,
        seconds=int(duration.total_seconds())
    )
    return JsonResponse({'is_success': True})

# Архивация проекта
# Исправлен баг (при архивации активного проекта он не снимался с активного состояния)
@require_POST
@login_required
def project_archive(request, id):
    try:
        project = Project.objects.get(id=id, user=request.user)
        # Проверяем, не является ли проект активным
        try:
            active_project = ActiveProject.objects.get(user=request.user)
            if active_project.project == project:
                # Сбрасываем активный проект
                active_project.project = None
                active_project.in_work = False
                active_project.save()
        except ActiveProject.DoesNotExist:
            pass

        project.is_archived = True
        project.save()
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': id}))
    except Project.DoesNotExist:
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': id}))

# Изменение статуса задачи с ограничением: только при запущенном таймере проекта
@require_POST
@login_required
def change_task_status(request, id):
    try:
        with transaction.atomic():
            task = Task.objects.select_for_update().get(id=id, project__user=request.user)
    except Task.DoesNotExist:
        return JsonResponse({'is_success': False, 'error': 'Задача не найдена'})

    # Запрет изменения задач, если проект на проверке или принят
    if task.project.review_status in ['in_review', 'approved']:
        return JsonResponse({'is_success': False, 'error': 'Проект на проверке/принят: изменение задач запрещено'})

    # Проверка: должен быть запущен какой-либо таймер пользователя (учитываем оба механизма)
    # Разрешаем переключаться между проектами или запускать таймер для задачи
    any_timer = ProjectTimer.objects.filter(user=request.user, in_work=True).first()
    any_active = ActiveProject.objects.filter(user=request.user, in_work=True).first()
    
    if not (any_timer or any_active):
        return JsonResponse({'is_success': False, 'error': 'Ни один таймер не запущен. Сначала запустите таймер проекта.'})

    # Линейный переход статусов: new -> in_progress -> done
    if task.status == 'new':
        task.status = 'in_progress'
        task.is_done = False
        # Останавливаем все другие таймеры пользователя и фиксируем время
        now = timezone.now()
        running = ProjectTimer.objects.filter(user=request.user, in_work=True)
        for rt in running:
            started_at = rt.last_started_at
            if started_at:
                duration = now - started_at
                TimeEntry.objects.create(
                    user=request.user,
                    project=rt.project,
                    task=rt.current_task,
                    started_at=started_at,
                    ended_at=now,
                    seconds=int(duration.total_seconds())
                )
            rt.in_work = False
            rt.current_task = None
            rt.save(update_fields=['in_work', 'current_task'])
        # Запускаем таймер по текущему проекту и привязываем к задаче
        timer, _ = ProjectTimer.objects.get_or_create(user=request.user, project=task.project)
        if not timer.in_work:
            timer.start()
        timer.current_task = task
        timer.save(update_fields=['current_task'])
        # Фиксируем момент старта задачи
        task.started_at = now
    elif task.status == 'in_progress':
        # Минимальная длительность 60 секунд, если таймер был запущен
        timer = ProjectTimer.objects.filter(user=request.user, project=task.project).first()
        now = timezone.now()
        base_start = task.started_at or (timer.last_started_at if (timer and timer.in_work and timer.current_task_id == task.id) else None)
        if base_start:
            worked = (now - base_start).total_seconds()
            if worked < 60:
                return JsonResponse({'is_success': False, 'error': 'Минимальная длительность работы над задачей — 1 минута'})
        task.status = 'done'
        task.is_done = True
        task.completed_at = now
        # Останавливаем таймер проекта и фиксируем запись времени для этой задачи
        if timer and timer.in_work and timer.current_task_id == task.id and timer.last_started_at:
            duration = now - timer.last_started_at
            TimeEntry.objects.create(
                user=request.user,
                project=task.project,
                task=task,
                started_at=timer.last_started_at,
                ended_at=now,
                seconds=int(duration.total_seconds())
            )
            timer.in_work = False
            timer.current_task = None
            timer.save(update_fields=['in_work', 'current_task'])
    else:
        # done: ничего не делаем (можно расширить логикой отката при необходимости)
        return JsonResponse({'is_success': True})
    update_fields = ['status', 'is_done']
    if task.status == 'done':
        update_fields.append('completed_at')
    if task.status == 'in_progress' and task.started_at:
        update_fields.append('started_at')
    task.save(update_fields=update_fields)
    return JsonResponse({'is_success': True})

# Запуск таймера для конкретного проекта (параллельно с другими)
@require_POST
@login_required
def project_timer_start(request):
    project_id = request.POST.get('project_id')
    try:
        project = Project.objects.get(id=project_id, user=request.user)
    except (Project.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'is_success': False, 'error': 'Проект не найден'})

    # Запрет старта таймера, если проект на проверке или принят
    if project.review_status in ['in_review', 'approved']:
        return JsonResponse({'is_success': False, 'error': 'Проект на проверке/принят: запуск таймера запрещён'})
    timer, _ = ProjectTimer.objects.get_or_create(user=request.user, project=project)
    if timer.in_work:
        return JsonResponse({'is_success': False, 'error': 'Таймер уже запущен'})
    timer.start()
    return JsonResponse({'is_success': True})

# Остановка таймера для конкретного проекта
@require_POST
@login_required
def project_timer_stop(request):
    project_id = request.POST.get('project_id')
    try:
        project = Project.objects.get(id=project_id, user=request.user)
    except (Project.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'is_success': False, 'error': 'Проект не найден'})

    timer = ProjectTimer.objects.filter(user=request.user, project=project).first()
    if not timer or not timer.in_work:
        return JsonResponse({'is_success': False, 'error': 'Таймер не запущен'})

    started_at = timer.last_started_at
    duration = timer.stop()
    # Обновляем общее время проекта
    project.total_time += duration
    project.save()
    TimeEntry.objects.create(
        user=request.user,
        project=project,
        started_at=started_at,
        ended_at=timezone.now(),
        seconds=int(duration.total_seconds())
    )
    return JsonResponse({'is_success': True, 'seconds': int(duration.total_seconds())})

# Project-level review workflow
class ProjectReviewQueueView(LoginRequiredMixin, ListView):
    template_name = 'workflow/project_review_queue.html'
    model = Project
    def get_queryset(self):
        role = getattr(getattr(self.request.user, 'profile', None), 'role', None)
        if role not in ['manager', 'sector_manager', 'director']:
            return self.model.objects.none()
        if role == 'director':
            # Директор видит проекты своих непосредственных подчиненных
            from accounts.models import Profile
            try:
                my_profile = self.request.user.profile
                subordinate_users = Profile.objects.filter(manager=my_profile).values_list('user_id', flat=True)
                return super().get_queryset().filter(user_id__in=subordinate_users, review_status='in_review')
            except Exception:
                return self.model.objects.none()
        # руководитель видит проекты подчиненных
        from accounts.models import Profile
        try:
            my_profile = self.request.user.profile
            subordinate_users = Profile.objects.filter(manager=my_profile).values_list('user_id', flat=True)
            return super().get_queryset().filter(user_id__in=subordinate_users, review_status='in_review')
        except Exception:
            return self.model.objects.none()

@require_POST
@login_required
def project_submit_review(request, pk):
    try:
        project = Project.objects.get(pk=pk, user=request.user)
    except Project.DoesNotExist:
        messages.error(request, 'Проект не найден')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    # Разрешаем отправку только если все задачи завершены
    if project.tasks.filter(status__in=['new', 'in_progress']).exists():
        messages.error(request, 'Нельзя отправить на проверку: не все задачи завершены')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    # Нельзя отправить, если запущены таймеры по проекту
    ptimer = ProjectTimer.objects.filter(user=request.user, project=project, in_work=True).exists()
    atimer = ActiveProject.objects.filter(user=request.user, project=project, in_work=True).exists()
    if ptimer or atimer:
        messages.error(request, 'Остановите таймер по этому проекту перед отправкой на проверку')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    # Валидация: нужен комментарий или хотя бы один файл
    submit_comment = request.POST.get('submit_comment', '').strip()
    files = request.FILES.getlist('files')
    if not submit_comment and not files:
        messages.error(request, 'Нужно добавить комментарий или хотя бы один файл для отправки на проверку')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    if submit_comment:
        project.submit_comment = submit_comment
    for f in files:
        ProjectAttachment.objects.create(project=project, file=f, uploaded_by=request.user)

    project.review_status = 'in_review'
    project.review_submitted_by = request.user
    project.review_submitted_at = timezone.now()
    project.save(update_fields=['review_status', 'review_submitted_by', 'review_submitted_at', 'submit_comment'])
    messages.success(request, 'Проект отправлен на проверку')
    return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))

# Защищенная выдача вложений проекта с проверкой прав
@login_required
def project_attachment_download(request, pk, attachment_id):
    project = get_object_or_404(Project, pk=pk)
    attachment = get_object_or_404(ProjectAttachment, pk=attachment_id, project=project)
    # Доступ: владелец проекта, его непосредственный руководитель (manager/sector_manager), директор, суперпользователь
    if request.user.is_superuser or project.user_id == request.user.id:
        pass
    else:
        role = getattr(getattr(request.user, 'profile', None), 'role', None)
        try:
            owner_manager_id = project.user.profile.manager_id
        except Exception:
            owner_manager_id = None
        allowed = (
            (role in ['manager', 'sector_manager'] and owner_manager_id == getattr(request.user, 'profile', None).id) or
            role == 'director'
        )
        if not allowed:
            messages.error(request, 'Нет доступа к файлу')
            return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    file_handle = attachment.file.open('rb')
    response = FileResponse(file_handle, as_attachment=True, filename=attachment.file.name.split('/')[-1])
    return response

@require_POST
@login_required
def project_review_approve(request, pk):
    role = getattr(getattr(request.user, 'profile', None), 'role', None)
    if role not in ['manager', 'sector_manager']:
        messages.error(request, 'Нет прав')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    try:
        project = Project.objects.get(pk=pk)
    except Project.DoesNotExist:
        messages.error(request, 'Проект не найден')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    # Дополнительные проверки подчиненности и самоутверждения
    try:
        reviewer_profile = request.user.profile
        owner_profile = project.user.profile
    except Exception:
        messages.error(request, 'Нет прав')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    # Запрет самоутверждения
    if project.user_id == request.user.id:
        messages.error(request, 'Нельзя принимать собственный проект')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    # Разрешения по ролям: менеджер/начальник сектора может только своих подчиненных
    if owner_profile.manager_id != reviewer_profile.id:
        messages.error(request, 'Можно принимать только проекты подчиненных')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    project.review_status = 'approved'
    project.is_archived = True
    project.reviewed_by = request.user
    project.reviewed_at = timezone.now()
    project.save(update_fields=['review_status', 'is_archived', 'reviewed_by', 'reviewed_at'])
    messages.success(request, 'Проект принят и помещен в архив')
    return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))

@require_POST
@login_required
def project_review_reject(request, pk):
    role = getattr(getattr(request.user, 'profile', None), 'role', None)
    if role not in ['manager', 'sector_manager']:
        messages.error(request, 'Нет прав')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    try:
        project = Project.objects.get(pk=pk)
    except Project.DoesNotExist:
        messages.error(request, 'Проект не найден')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    # Дополнительные проверки подчиненности и самоутверждения
    try:
        reviewer_profile = request.user.profile
        owner_profile = project.user.profile
    except Exception:
        messages.error(request, 'Нет прав')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    if project.user_id == request.user.id:
        messages.error(request, 'Нельзя возвращать собственный проект')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    if owner_profile.manager_id != reviewer_profile.id:
        messages.error(request, 'Можно возвращать только проекты подчиненных')
        return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))
    comment = request.POST.get('review_comment', '').strip()
    project.review_status = 'rejected'
    project.review_comment = comment
    project.reviewed_by = request.user
    project.reviewed_at = timezone.now()
    project.save(update_fields=['review_status', 'review_comment', 'reviewed_by', 'reviewed_at'])
    messages.info(request, 'Проект возвращен')
    return HttpResponseRedirect(reverse_lazy('project_detail', kwargs={'pk': pk}))

@require_GET
@login_required
def project_review_count(request):
    role = getattr(getattr(request.user, 'profile', None), 'role', None)
    if role not in ['manager', 'sector_manager', 'director']:
        return JsonResponse({'count': 0})
    if role == 'director':
        # Директор видит проекты своих непосредственных подчиненных
        from accounts.models import Profile
        try:
            my_profile = request.user.profile
            subordinate_users = Profile.objects.filter(manager=my_profile).values_list('user_id', flat=True)
            count = Project.objects.filter(user_id__in=subordinate_users, review_status='in_review').count()
        except Exception:
            count = 0
    else:
        from accounts.models import Profile
        try:
            my_profile = request.user.profile
            subordinate_users = Profile.objects.filter(manager=my_profile).values_list('user_id', flat=True)
            count = Project.objects.filter(user_id__in=subordinate_users, review_status='in_review').count()
        except Exception:
            count = 0
    return JsonResponse({'count': count})

@require_POST
@login_required
def stop_all_timers_on_close(request):
    """
    Stops all running timers for the current user when the application is closed.
    This view is called automatically via JavaScript beforeunload event.
    """
    now = timezone.now()
    
    # Stop ActiveProject timer if running
    active_project = ActiveProject.objects.filter(user=request.user, in_work=True).first()
    if active_project and active_project.project and active_project.last_started_at:
        duration = now - active_project.last_started_at
        active_project.in_work = False
        active_project.project.total_time += duration
        active_project.save()
        active_project.project.save()
        
        # Create TimeEntry for the session
        TimeEntry.objects.create(
            user=request.user,
            project=active_project.project,
            started_at=active_project.last_started_at,
            ended_at=now,
            seconds=int(duration.total_seconds())
        )
    
    # Stop all ProjectTimer instances that are running
    running_timers = ProjectTimer.objects.filter(user=request.user, in_work=True)
    for timer in running_timers:
        if timer.last_started_at:
            duration = now - timer.last_started_at
            timer.in_work = False
            timer.save()
            
            # Update project total time
            timer.project.total_time += duration
            timer.project.save()
            
            # Create TimeEntry for the session
            TimeEntry.objects.create(
                user=request.user,
                project=timer.project,
                task=timer.current_task,
                started_at=timer.last_started_at,
                ended_at=now,
                seconds=int(duration.total_seconds())
            )
    
    return JsonResponse({'is_success': True, 'stopped_timers': running_timers.count() + (1 if active_project else 0)})