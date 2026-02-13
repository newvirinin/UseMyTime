from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.forms import UserRegistrationForm
from accounts.models import Profile, Department


class ProfileViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="john",
            email="john@example.com",
            password="testpass123",
        )

    def test_profile_view_requires_authentication(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_profile_view_creates_profile_for_authenticated_user(self):
        logged_in = self.client.login(username="john", password="testpass123")
        self.assertTrue(logged_in)

        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")

        # Профиль создаётся автоматически при первом входе
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.role, "employee")


class MyTeamViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name="Отдел разработки")

        cls.manager_user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="managerpass",
        )
        cls.manager_profile = Profile.objects.get(user=cls.manager_user)
        cls.manager_profile.role = "manager"
        cls.manager_profile.department = cls.department
        cls.manager_profile.save()

        cls.employee_user = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="employeepass",
        )
        cls.employee_profile = Profile.objects.get(user=cls.employee_user)
        cls.employee_profile.role = "employee"
        cls.employee_profile.department = cls.department
        cls.employee_profile.manager = cls.manager_profile
        cls.employee_profile.save()

    def test_my_team_view_lists_subordinates(self):
        self.client.login(username="manager", password="managerpass")
        response = self.client.get(reverse("my_team"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/my_team.html")

        team_tasks = response.context.get("team_tasks")
        self.assertIsInstance(team_tasks, list)
        self.assertEqual(len(team_tasks), 1)
        self.assertEqual(team_tasks[0]["employee"], self.employee_profile)


class RegisterFormTests(TestCase):
    def test_registration_form_rejects_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            email="duplicate@example.com",
            password="password123",
        )

        form = UserRegistrationForm(
            data={
                "username": "newuser",
                "email": "duplicate@example.com",
                "password": "Testpass123!",
                "password2": "Testpass123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class EditEmployeeViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name="Отдел продаж")

        cls.manager_user = User.objects.create_user(
            username="dept_manager",
            email="dept_manager@example.com",
            password="managerpass",
        )
        cls.manager_profile = Profile.objects.get(user=cls.manager_user)
        cls.manager_profile.role = "manager"
        cls.manager_profile.department = cls.department
        cls.manager_profile.save()

        cls.other_user = User.objects.create_user(
            username="dept_employee",
            email="dept_employee@example.com",
            password="employeepass",
        )
        cls.other_profile = Profile.objects.get(user=cls.other_user)
        cls.other_profile.role = "employee"
        cls.other_profile.department = cls.department
        cls.other_profile.manager = cls.manager_profile
        cls.other_profile.save()

        cls.employee_user = User.objects.create_user(
            username="plain_employee",
            email="plain_employee@example.com",
            password="plainpass",
        )
        employee_profile = Profile.objects.get(user=cls.employee_user)
        employee_profile.role = "employee"
        employee_profile.department = cls.department
        employee_profile.save()

    def test_edit_employee_requires_manager_role(self):
        self.client.login(username="plain_employee", password="plainpass")
        response = self.client.get(reverse("edit_employee", args=[self.other_user.id]))

        # Декоратор перенаправляет пользователя без роли на главную
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("index"))

    def test_manager_can_open_edit_employee_page(self):
        self.client.login(username="dept_manager", password="managerpass")
        response = self.client.get(reverse("edit_employee", args=[self.other_user.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/edit.html")
        self.assertIn("user_form", response.context)
        self.assertIn("profile_form", response.context)
