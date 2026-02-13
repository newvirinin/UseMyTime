from django.contrib import admin
from .models import Profile, Department, UserProxy, GroupProxy
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django import forms
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm, UserCreationForm

# Убираем самостоятельные разделы Profile и Department из админки (оставляем только inline у Пользователя)
try:
    admin.site.unregister(Profile)
except admin.sites.NotRegistered:
    pass
try:
    admin.site.unregister(Department)
except admin.sites.NotRegistered:
    pass
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name']

# Встраивание профиля на страницу пользователя
class ManagerChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Фамилия Имя Отчество, должность
        fio = f"{obj.user.last_name} {obj.user.first_name} {obj.surname}".strip()
        pos = (obj.position or '').strip()
        return f"{fio}, {pos}" if pos else fio


class ProfileInlineForm(forms.ModelForm):
    manager = ManagerChoiceField(queryset=Profile.objects.none(), required=False, label='Начальник')

    class Meta:
        model = Profile
        fields = ['department', 'position', 'phone_internal', 'photo', 'role', 'manager']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Сортировка по должности, затем по Фамилии и Имени
        self.fields['manager'].queryset = (
            Profile.objects.select_related('user')
            .order_by('position', 'user__last_name', 'user__first_name')
        )


class ProfileInline(admin.StackedInline):
    model = Profile
    form = ProfileInlineForm
    can_delete = False
    extra = 0
    fields = ('department', 'position', 'phone_internal', 'photo', 'role', 'manager')

class UserChangeForm(DjangoUserChangeForm):
    surname = forms.CharField(label='Отчество', required=False)

    class Meta:
        model = UserProxy
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            try:
                self.fields['surname'].initial = getattr(self.instance.profile, 'surname', '')
            except Profile.DoesNotExist:
                pass

    def save(self, commit=True):
        user = super().save(commit)
        # ensure profile exists
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.surname = self.cleaned_data.get('surname', '')
        if commit:
            profile.save()
        else:
            # If not committing here, caller should save profile separately
            pass
        return user

class UserCreateForm(UserCreationForm):
    first_name = forms.CharField(label='Имя', max_length=150, required=False)
    last_name = forms.CharField(label='Фамилия', max_length=150, required=False)
    email = forms.EmailField(label='Email', required=False)
    surname = forms.CharField(label='Отчество', max_length=150, required=False)

    class Meta(UserCreationForm.Meta):
        model = UserProxy
        fields = ('username',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data.get('email', '')
        if commit:
            user.save()
            # create/update profile with surname
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.surname = self.cleaned_data.get('surname', '')
            profile.save()
        return user

class UserAdmin(BaseUserAdmin):
    model = UserProxy
    form = UserChangeForm
    add_form = UserCreateForm
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'last_name', 'first_name', 'surname_col', 'department_col', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__surname')
    # Place patronymic (Отчество) under Personal info section in order: Фамилия, Имя, Отчество
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('last_name', 'first_name', 'surname', 'email')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'last_name', 'first_name', 'surname', 'email'),
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Ensure profile exists for newly created users
        profile, _ = Profile.objects.get_or_create(user=obj)
        # Redundantly persist surname from main form if present
        if hasattr(form, 'cleaned_data') and 'surname' in form.cleaned_data:
            cd_surname = form.cleaned_data.get('surname')
            if cd_surname is not None:
                profile.surname = cd_surname
                profile.save()

    def get_inline_instances(self, request, obj=None):
        # Не показываем инлайны при создании пользователя (obj is None), чтобы избежать ошибок
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

    def surname_col(self, obj):
        return getattr(getattr(obj, 'profile', None), 'surname', '')
    surname_col.short_description = 'Отчество'

    def department_col(self, obj):
        dept = getattr(getattr(obj, 'profile', None), 'department', None)
        return getattr(dept, 'name', '') if dept else ''
    department_col.short_description = 'Отдел'

# Пере-регистрация пользователей через прокси, чтобы они отображались в приложении 'Профили'
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(UserProxy, UserAdmin)