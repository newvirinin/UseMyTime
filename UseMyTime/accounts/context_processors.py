from .models import Profile
from projects.models import ActiveProject, Project

def profile_context(request):
    """Context processor для безопасного доступа к профилю пользователя"""
    context = {}
    if request.user.is_authenticated:
        # Получаем или создаем профиль, если его нет
        try:
            profile, created = Profile.objects.get_or_create(user=request.user)
            context['user_profile'] = profile
            # Данные об активном проекте для глобального таймера
            try:
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
            except ActiveProject.DoesNotExist:
                context['active_project_info'] = None
            # Счетчик проектов на проверке для руководителей
            try:
                role = getattr(profile, 'role', None)
                if role in ['manager', 'sector_manager', 'director']:
                    if role == 'director':
                        context['review_queue_count'] = Project.objects.filter(review_status='in_review').count()
                    else:
                        subs = Profile.objects.filter(manager=profile).values_list('user_id', flat=True)
                        context['review_queue_count'] = Project.objects.filter(user_id__in=list(subs), review_status='in_review').count()
                else:
                    context['review_queue_count'] = 0
            except Exception:
                context['review_queue_count'] = 0
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

