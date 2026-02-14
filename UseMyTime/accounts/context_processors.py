from .models import Profile
from projects.models import ActiveProject, Project, ProjectTimer

def profile_context(request):
    """Context processor для безопасного доступа к профилю пользователя"""
    context = {}
    if request.user.is_authenticated:
        # Получаем или создаем профиль, если его нет
        try:
            profile, created = Profile.objects.get_or_create(user=request.user)
            context['user_profile'] = profile
            # Данные об активном проекте для глобального таймера (используем новый механизм ProjectTimer)
            try:
                # Ищем запущенный таймер
                running_timer = ProjectTimer.objects.select_related('project').filter(
                    user=request.user, 
                    in_work=True
                ).first()
                
                if running_timer and running_timer.project:
                    base_seconds = int(running_timer.project.total_time.total_seconds())
                    started_at_epoch = int(running_timer.last_started_at.timestamp()) if running_timer.last_started_at else None
                    context['active_project_info'] = {
                        'project': running_timer.project,
                        'base_seconds': base_seconds,
                        'started_at_epoch': started_at_epoch,
                        'in_work': running_timer.in_work,
                    }
                else:
                    # Если нет запущенных таймеров, пробуем старый механизм как запасной вариант
                    active = ActiveProject.objects.select_related('project').get(user=request.user)
                    if active and active.project:
                        base_seconds = int(active.project.total_time.total_seconds())
                        started_at_epoch = int(active.last_started_at.timestamp()) if active.in_work and active.last_started_at else None
                        context['active_project_info'] = {
                            'project': active.project,
                            'base_seconds': base_seconds,
                            'started_at_epoch': started_at_epoch,
                            'in_work': active.in_work,
                        }
                    else:
                        context['active_project_info'] = None
            except (ProjectTimer.DoesNotExist, ActiveProject.DoesNotExist):
                context['active_project_info'] = None
            except Exception as e:
                # Если есть запущенные таймеры, но произошла ошибка, попробуем найти любой
                try:
                    any_timer = ProjectTimer.objects.select_related('project').filter(
                        user=request.user
                    ).first()
                    if any_timer and any_timer.project:
                        base_seconds = int(any_timer.project.total_time.total_seconds())
                        context['active_project_info'] = {
                            'project': any_timer.project,
                            'base_seconds': base_seconds,
                            'started_at_epoch': None,
                            'in_work': False,
                        }
                    else:
                        context['active_project_info'] = None
                except Exception:
                    context['active_project_info'] = None
                    
            # Счетчик проектов на проверке для руководителей
            try:
                role = getattr(profile, 'role', None)
                if role in ['manager', 'sector_manager', 'director']:
                    if role == 'director':
                        # Директор видит проекты своих непосредственных подчиненных
                        subs = Profile.objects.filter(manager=profile).values_list('user_id', flat=True)
                        context['review_queue_count'] = Project.objects.filter(user_id__in=list(subs), review_status='in_review').count()
                    else:
                        subs = Profile.objects.filter(manager=profile).values_list('user_id', flat=True)
                        context['review_queue_count'] = Project.objects.filter(user_id__in=list(subs), review_status='in_review').count()
                else:
                    context['review_queue_count'] = 0

                # Счетчик проектов, требующих внимания (возвращенные с проверки)
                context['attention_projects_count'] = Project.objects.filter(
                    user=request.user, 
                    review_status='rejected',
                    is_archived=False
                ).count()
            except Exception:
                context['review_queue_count'] = 0
                context['attention_projects_count'] = 0
        except Exception:
            # Если возникла ошибка, возвращаем None
            context['user_profile'] = None
            context['active_project_info'] = None
            context['review_queue_count'] = 0
    else:
        # Для неаутентифицированных пользователей возвращаем None
        context['user_profile'] = None
        context['active_project_info'] = None
        context['review_queue_count'] = 0
    return context

