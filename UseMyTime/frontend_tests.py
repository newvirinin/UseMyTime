#!/usr/bin/env python3
"""
Тестирование клиентской части приложения UseMyTime25
Проверка шаблонов, статических файлов и пользовательского интерфейса
"""

import os
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import Profile, Department
from projects.models import Project, Task


class TemplateRenderingTests(TestCase):
    """Тесты корректности рендеринга шаблонов"""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cls.department = Department.objects.create(name='Тестовый отдел')
        cls.profile = Profile.objects.get(user=cls.user)
        cls.profile.department = cls.department
        cls.profile.save()
    
    def test_index_page_renders_correctly(self):
        """Тест корректности рендеринга главной страницы"""
        response = self.client.get(reverse('index'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'UseMyTime')
    
    def test_login_page_renders_form(self):
        """Тест отображения формы входа"""
        response = self.client.get(reverse('login'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertContains(response, 'username')
        self.assertContains(response, 'password')
        self.assertContains(response, 'type="submit"')
    
    def test_profile_page_displays_user_info(self):
        """Тест отображения информации пользователя в профиле"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        self.assertContains(response, 'testuser')
    
    def test_project_list_page_renders(self):
        """Тест рендеринга страницы списка проектов"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('project_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/list.html')


class StaticFilesTests(TestCase):
    """Тесты доступности статических файлов"""
    
    def test_css_file_accessible(self):
        """Тест доступности CSS файлов"""
        from django.conf import settings
        import os
        css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'style.css')
        self.assertTrue(os.path.exists(css_path), 
                       f"CSS файл должен существовать по пути {css_path}")
    
    def test_static_files_directory_exists(self):
        """Тест существования директории статических файлов"""
        from django.conf import settings
        static_dir = os.path.join(settings.BASE_DIR, 'static')
        self.assertTrue(os.path.exists(static_dir))


class UIComponentTests(TestCase):
    """Тесты компонентов пользовательского интерфейса"""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='uiuser',
            email='ui@example.com',
            password='uipass123'
        )
        cls.department = Department.objects.create(name='UI Отдел')
        cls.profile = Profile.objects.get(user=cls.user)
        cls.profile.department = cls.department
        cls.profile.save()
        
        cls.project = Project.objects.create(
            user=cls.user,
            title='Тестовый проект',
            description='Описание тестового проекта'
        )
    
    def test_navigation_menu_present(self):
        """Тест наличия навигационного меню"""
        self.client.login(username='uiuser', password='uipass123')
        response = self.client.get(reverse('profile'))
        
        self.assertContains(response, 'nav')
    
    def test_project_card_displays_correctly(self):
        """Тест корректного отображения карточки проекта"""
        self.client.login(username='uiuser', password='uipass123')
        response = self.client.get(reverse('project_list'))
        
        self.assertContains(response, 'Тестовый проект')
        self.assertContains(response, 'Описание тестового проекта')
    
    def test_form_validation_messages_display(self):
        """Тест отображения сообщений валидации форм"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'invalid-email',  # Невалидный email
            'password': 'pass',
            'password2': 'pass'
        })
        
        # Форма должна показать ошибки валидации
        self.assertEqual(response.status_code, 200)
        # Проверяем наличие сообщения об ошибке в ответе
        self.assertContains(response, 'электронной почты', status_code=200)


class ResponsiveDesignTests(TestCase):
    """Тесты адаптивности дизайна"""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='responsive',
            email='responsive@example.com',
            password='resppass123'
        )
    
    def test_viewport_meta_tag_present(self):
        """Тест наличия viewport meta тега для адаптивности"""
        response = self.client.get(reverse('index'))
        
        # Проверяем наличие viewport в HTML
        self.assertContains(response, 'viewport')
    
    def test_bootstrap_classes_used(self):
        """Тест использования Bootstrap классов для адаптивности"""
        self.client.login(username='responsive', password='resppass123')
        response = self.client.get(reverse('profile'))
        
        # Проверяем наличие Bootstrap классов
        self.assertContains(response, 'container')


class JavaScriptFunctionalityTests(TestCase):
    """Тесты JavaScript функциональности"""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='jsuser',
            email='js@example.com',
            password='jspass123'
        )
        cls.project = Project.objects.create(
            user=cls.user,
            title='JS Проект',
            description='Проект для тестирования JS'
        )
    
    def test_project_detail_page_has_timer_elements(self):
        """Тест наличия элементов таймера на странице проекта"""
        self.client.login(username='jsuser', password='jspass123')
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        
        self.assertEqual(response.status_code, 200)
        # Проверяем наличие кнопок управления таймером
        self.assertContains(response, 'Старт', html=False)


class AccessibilityTests(TestCase):
    """Тесты доступности интерфейса"""
    
    def test_forms_have_labels(self):
        """Тест наличия labels у полей форм"""
        response = self.client.get(reverse('login'))
        
        # Проверяем наличие label для username
        self.assertContains(response, '<label')
    
    def test_images_have_alt_attributes(self):
        """Тест наличия alt атрибутов у изображений"""
        self.user = User.objects.create_user(
            username='altuser',
            email='alt@example.com',
            password='altpass123'
        )
        self.client.login(username='altuser', password='altpass123')
        response = self.client.get(reverse('profile'))
        
        # Если есть изображения, они должны иметь alt
        if '<img' in response.content.decode():
            self.assertContains(response, 'alt=')


if __name__ == '__main__':
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    django.setup()
    
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    runner.run_tests(['frontend_tests'])
