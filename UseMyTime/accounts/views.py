from django.http import HttpResponse
import hashlib
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, UserEditForm, ProfileEditForm
from .models import Profile, Department
from django.contrib import messages
from django.views.decorators.http import require_POST

# Добавлены библиотеки
from projects.models import Project, Task
from django.utils import timezone
from django.template.loader import render_to_string
from weasyprint import HTML # Библиотека для формирования отчетов
from .decorators import role_required # Кастомный декоратор для проверки роли пользователя

# Отображение профиля
@login_required
def profile(request):
    # Получаем или создаем профиль, если его нет
    profile_obj, created = Profile.objects.get_or_create(user=request.user)
    return render(request,
                  'accounts/profile.html',
                  {'section': 'profile'})

# Регистрация пользователя
def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(
                user_form.cleaned_data['password'])
            new_user.save()
            Profile.objects.get_or_create(user=new_user)
            return render(request,
                          'accounts/register_done.html',
                          {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request,
                  'accounts/register.html',
                  {'user_form': user_form})

# Редактирование данных пользователя
@login_required
def edit(request):
    # Получаем или создаем профиль, если его нет
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user,
                                 data=request.POST)
        profile_form = ProfileEditForm(
                                    instance=profile,
                                    data=request.POST,
                                    files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile') # Исправлено (теперь после редактирования профиля пользователя перенаправляет обратно на страницу его профиля)
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(
                                    instance=profile)
    return render(request,
                  'accounts/edit.html',
                  {'user_form': user_form,
                   'profile_form': profile_form})

# Добавлена страница отдела для начальников
@login_required
@role_required(['manager', 'sector_manager'])
def my_team(request):
    profile = request.user.profile

    # Все подчинённые (кто имеет этого пользователя как manager)
    team = profile.subordinates.all()

    # Собираем задачи для каждого сотрудника
    team_tasks = []
    for employee in team:
        # Находим все проекты, где employee.user — владелец
        employee_projects = Project.objects.filter(user=employee.user, is_archived=False)
        # Находим все задачи из этих проектов
        tasks = Task.objects.filter(project__in=employee_projects)

        team_tasks.append({
            'employee': employee,
            'tasks': tasks
        })

    context = {
        'team_tasks': team_tasks,
    }
    return render(request, 'accounts/my_team.html', context)

    

# Добавлена возможность редактировать профили добалвенных сотрудников
@login_required
@role_required(['manager', 'sector_manager'])
def edit_employee(request, user_id):
    """Редактирование профиля сотрудника (только для своего отдела)"""
    user = User.objects.get(id=user_id)
    profile = request.user.profile

    # Проверяем, что сотрудник в подчинении
    if user.profile.manager != profile and profile.role != 'director':
        messages.error(request, "Нет доступа.")
        return redirect('my_team')
    # Дополнительная проверка: отдел должен совпадать (кроме директора)
    if profile.role != 'director' and user.profile.department != profile.department:
        messages.error(request, "Нет доступа к сотруднику из другого отдела.")
        return redirect('my_team')

    if request.method == 'POST':
        user_form = UserEditForm(instance=user,
                                 data=request.POST)
        profile_form = ProfileEditForm(
            instance=user.profile,
            data=request.POST,
            files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f"Профиль { user.last_name } { user.first_name } ({ user.profile.position }) успешно обновлён.")
            return redirect('my_team')
    else:
        user_form = UserEditForm(instance=user)
        profile_form = ProfileEditForm(
            instance=user.profile)

    return render(request, 'accounts/edit.html', {'user_form': user_form,
                   'profile_form': profile_form})

# Страница "Отчеты по компании" для директора
@login_required
@role_required(['director'])
def company_reports(request):
    departments = Department.objects.all().order_by('name')
    employees = Profile.objects.select_related('user', 'department').exclude(user__is_superuser=True).exclude(user__is_staff=True).order_by('user__last_name', 'user__first_name')
    # Дефолтный период: текущий месяц
    now = timezone.now()
    default_start = now.replace(day=1).date()
    # следующий месяц 1-е минус день
    if now.month == 12:
        next_month = now.replace(year=now.year+1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month+1, day=1)
    default_end = (next_month - timezone.timedelta(days=1)).date()

    context = {
        'departments': departments,
        'employees': employees,
        'now': now,
        'default_start_date': default_start.strftime('%Y-%m-%d'),
        'default_end_date': default_end.strftime('%Y-%m-%d'),
    }
    return render(request, 'accounts/company_reports.html', context)

# Добавлена возможность генерировать отчет по отделу
@login_required
@role_required(['manager', 'sector_manager', 'director'])
def generate_report(request):
    profile = request.user.profile

    # Если директор, можно выбрать отдел (или все отделы)
    report_department = None
    if profile.role == 'director':
        dept_id = request.GET.get('department')
        if dept_id:
            report_department = get_object_or_404(Department, id=dept_id)
            team = Profile.objects.filter(department=report_department)
        else:
            team = Profile.objects.all()
    else:
        # Для начальника — только его подчинённые
        team = Profile.objects.filter(manager=profile)

    # Период (необязательный)
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except Exception:
            start_date = None
    if end_date_str:
        try:
            end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except Exception:
            end_date = None

    team_report = []
    total_department_time = 0
    total_department_tasks = 0

    for employee in team:
        user = employee.user

        # Только неархивные и принятые проекты
        projects = Project.objects.filter(user=user, is_archived=False, review_status='approved')
        completed_tasks = Task.objects.filter(
            project__in=projects,
            is_done=True
        ).select_related('project')
        if start_date:
            completed_tasks = completed_tasks.filter(completed_at__date__gte=start_date)
        if end_date:
            completed_tasks = completed_tasks.filter(completed_at__date__lte=end_date)

        employee_data = {
            'employee': employee,
            'project_data': [],
            'total_hours': 0,
            'total_minutes': 0,
            'total_tasks': completed_tasks.count(),
            'work_days': 0,
        }

        total_seconds = 0

        for project in projects:
            tasks = completed_tasks.filter(project=project)
            if tasks.exists():
                proj_seconds = int(project.total_time.total_seconds())
                total_seconds += proj_seconds
                hours, minutes, seconds = project.get_hours_minutes_seconds()

                # Дата завершения — дата последней выполненной задачи
                last_task = tasks.order_by('-completed_at').first()

                employee_data['project_data'].append({
                    'project': project,
                    'tasks': tasks,
                    'hours': hours,
                    'minutes': minutes,
                    'seconds': seconds,
                    'created_at': project.created_at,
                    'completed_at': last_task.completed_at,
                })

        # Общее время по сотруднику
        employee_data['total_hours'] = total_seconds // 3600
        employee_data['total_minutes'] = (total_seconds % 3600) // 60
        employee_data['total_seconds'] = total_seconds % 60
        # Нормированные отработанные дни: 1 день = 8 часов
        employee_data['work_days'] = round(total_seconds / (8 * 3600), 2)
        total_department_time += total_seconds
        total_department_tasks += employee_data['total_tasks']

        team_report.append(employee_data)

    # Общее время по отделу
    dept_total_hours = total_department_time // 3600
    dept_total_minutes = (total_department_time % 3600) // 60

    # Если отчет по всей компании, группируем по отделам для подсчета итогов
    department_totals = []
    if not report_department:
        from collections import defaultdict
        dept_data = defaultdict(lambda: {'tasks': 0, 'seconds': 0, 'employees': []})
        
        for employee_data in team_report:
            dept = employee_data['employee'].department
            dept_key = dept.name if dept else 'Без отдела'
            dept_data[dept_key]['tasks'] += employee_data['total_tasks']
            dept_data[dept_key]['seconds'] += employee_data['total_hours'] * 3600 + employee_data['total_minutes'] * 60 + employee_data['total_seconds']
            dept_data[dept_key]['employees'].append(employee_data)
        
        for dept_name, data in dept_data.items():
            total_seconds = data['seconds']
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            department_totals.append({
                'name': dept_name,
                'tasks': data['tasks'],
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds,
                'employees': data['employees']
            })

    # Гарантируем наличие session_key для штампа ПЭП
    if not request.session.session_key:
        request.session.save()
    session_id = request.session.session_key

    # Дата формирования (единая для отображения и подписи)
    now_dt = timezone.now()

    # Отпечаток подписи: SHA-256(session_id + '|' + YYYY-MM-DD)
    signature_source = f"{session_id}|{now_dt.strftime('%Y-%m-%d')}".encode('utf-8')
    signature_hash = hashlib.sha256(signature_source).hexdigest()

    signature_valid_from = now_dt
    signature_valid_to = now_dt + timedelta(days=365)

    context = {
        'manager': profile,
        'team_report': team_report,
        'dept_total_hours': dept_total_hours,
        'dept_total_minutes': dept_total_minutes,
        'dept_total_tasks': total_department_tasks,
        'dept_total_seconds': total_department_time % 60,
        'now': now_dt,
        'author': request.user.profile,
        'report_department': report_department,
        'department_totals': department_totals,
        'session_id': session_id,
        'signature_hash': signature_hash,
        'signature_valid_from': signature_valid_from,
        'signature_valid_to': signature_valid_to,
        'start_date': start_date,
        'end_date': end_date,
    }

    # Если запрос на PDF
    if request.GET.get('format') == 'pdf':
        # Используем разные шаблоны для отчета по отделу и по компании
        if report_department:
            template_name = 'accounts/team_report.html'
            filename = f'отчет_отдела_{report_department.name}_{timezone.now().strftime("%Y%m%d")}.pdf'
        else:
            template_name = 'accounts/company_report.html'
            filename = f'отчет_компании_{timezone.now().strftime("%Y%m%d")}.pdf'
        
        html_string = render_to_string(template_name, context)
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        result = html.write_pdf()

        response = HttpResponse(result, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    # Используем разные шаблоны для отображения
    if report_department:
        template_name = 'accounts/team_report.html'
    else:
        template_name = 'accounts/company_report.html'
    
    return render(request, template_name, context)

# Добавлена возможность генерировать отчет по каждому сотруднику отдельно
@login_required
#@role_required(['manager'])
def employee_report(request, employee_id):
    # Получаем сотрудника
    employee = get_object_or_404(Profile, id=employee_id)
    user = employee.user
    requester = request.user
    requester_profile = requester.profile

    # Проверка прав доступа:
    # - суперпользователь всегда может
    # - директор всегда может
    # - сам сотрудник может смотреть свой отчёт
    # - начальник сотрудника (из того же отдела) может
    allowed = False
    if requester.is_superuser:
        allowed = True
    elif requester_profile.role == 'director':
        allowed = True
    elif user.id == requester.id:
        allowed = True
    elif requester_profile.role in ['manager', 'sector_manager'] and employee.manager_id == requester_profile.id:
        allowed = True

    if not allowed:
        messages.error(request, "Нет доступа к отчёту этого сотрудника.")
        # Менеджеров/директоров ведём в их отдел, остальных — в профиль
        if requester_profile.role in ['manager', 'sector_manager', 'director']:
            return redirect('my_team')
        return redirect('profile')

    # Период (необязательный)
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except Exception:
            start_date = None
    if end_date_str:
        try:
            end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except Exception:
            end_date = None

    # Только неархивные и принятые проекты
    projects = Project.objects.filter(user=user, is_archived=False, review_status='approved')

    # Только выполненные задачи
    completed_tasks = Task.objects.filter(
        project__in=projects,
        is_done=True
    ).select_related('project')
    if start_date:
        completed_tasks = completed_tasks.filter(completed_at__date__gte=start_date)
    if end_date:
        completed_tasks = completed_tasks.filter(completed_at__date__lte=end_date)

    # Подготовка данных: группировка по проектам
    report_data = []
    total_time_seconds = 0

    for project in projects:
        tasks = completed_tasks.filter(project=project)
        if tasks.exists():
            hours, minutes, seconds = project.get_hours_minutes_seconds()  # [ч, м]
            total_time_seconds += int(project.total_time.total_seconds())

            report_data.append({
                'project': project,
                'tasks': tasks,
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds,
                'created_at': project.created_at,
                # Завершение — дата последней выполненной задачи
                'completed_at': tasks.order_by('-completed_at').first().completed_at,
            })

    # Общее время
    total_hours = total_time_seconds // 3600
    total_minutes = (total_time_seconds % 3600) // 60
    work_days = round(total_time_seconds / (8 * 3600), 2)

    # Подготовка данных для штампа ПЭП
    if not request.session.session_key:
        request.session.save()
    session_id = request.session.session_key
    now_dt = timezone.now()
    signature_source = f"{session_id}|{now_dt.strftime('%Y-%m-%d')}".encode('utf-8')
    signature_hash = hashlib.sha256(signature_source).hexdigest()
    signature_valid_from = now_dt
    signature_valid_to = now_dt + timedelta(days=365)

    context = {
        'employee': employee,
        'report_data': report_data,
        'completed_tasks': completed_tasks,
        'total_hours': total_hours,
        'total_minutes': total_minutes,
        'total_seconds': total_time_seconds,
        'work_days': work_days,
        'now': now_dt,
        'author': request.user.profile,
        'session_id': session_id,
        'signature_hash': signature_hash,
        'signature_valid_from': signature_valid_from,
        'signature_valid_to': signature_valid_to,
        'start_date': start_date,
        'end_date': end_date,
    }

    # Если запрос на PDF
    if request.GET.get('format') == 'pdf':
        html_string = render_to_string('accounts/employee_report.html', context)
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        result = html.write_pdf()

        response = HttpResponse(result, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="отчет_{employee.user.last_name}_{now_dt.strftime("%Y%m%d")}.pdf"'
        return response

    return render(request, 'accounts/employee_report.html', context)