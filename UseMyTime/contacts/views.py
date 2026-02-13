from django.shortcuts import render, HttpResponseRedirect
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from .models import Question

# Страница контактов: форма вопроса разработчикам
@login_required
def contacts(request):
    user = request.user
    profile = getattr(user, 'profile', None)
    patronymic = getattr(profile, 'surname', '') if profile else ''
    default_name = f"{user.last_name} {user.first_name} {patronymic}".strip()
    default_email = user.email
    return render(request, 'contacts/index.html', {
        'default_name': default_name,
        'default_email': default_email,
    })

# Задание вопроса разработчикам (можно посмотреть в админке)
@login_required
def ask(request):
    if request.method == 'POST':
        user = request.user
        body = request.POST.get('body', '').strip()
        if body:
            Question.objects.create(user=user, body=body)
            return render(request, 'contacts/ask_success.html', {})
        return HttpResponseRedirect(reverse_lazy('contacts'))
    return HttpResponseRedirect(reverse_lazy('contacts'))

