#!/usr/bin/env python3
import requests
import subprocess
import json
import time
from datetime import datetime

class ServerTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_cases = []
        self.results = []
        
    def add_test_case(self, name, expected_result, test_function):
        """Добавление тест-кейса"""
        self.test_cases.append({
            'name': name,
            'expected': expected_result,
            'function': test_function
        })
        
    def run_test(self, test_case):
        """Выполнение одного теста"""
        start_time = time.time()
        try:
            actual_result = test_case['function']()
            end_time = time.time()
            
            success = actual_result == test_case['expected']
            
            result = {
                'name': test_case['name'],
                'expected': test_case['expected'],
                'actual': actual_result,
                'success': success,
                'duration': end_time - start_time,
                'timestamp': datetime.now().isoformat()
            }
            
            self.results.append(result)
            return result
            
        except Exception as e:
            result = {
                'name': test_case['name'],
                'expected': test_case['expected'],
                'actual': f'ERROR: {str(e)}',
                'success': False,
                'duration': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
            self.results.append(result)
            return result
    
    def test_main_page(self):
        """Тест главной страницы"""
        response = requests.get(f"{self.base_url}/")
        return response.status_code == 200
        
    def test_login_page(self):
        """Тест страницы входа"""
        response = requests.get(f"{self.base_url}/account/login/")
        return response.status_code == 200 and "login" in response.text.lower()
        
    def test_projects_page(self):
        """Тест страницы проектов"""
        response = requests.get(f"{self.base_url}/projects/")
        return response.status_code == 200
        
    def test_static_files(self):
        """Тест статических файлов"""
        response = requests.get(f"{self.base_url}/static/css/style.css")
        return response.status_code == 200
        
    def test_django_check(self):
        """Тест проверки Django"""
        result = subprocess.run(['python3', 'manage.py', 'check'], 
                              capture_output=True, text=True, timeout=30)
        return result.returncode == 0
        
    def test_migrations(self):
        """Тест миграций"""
        result = subprocess.run(['python3', 'manage.py', 'showmigrations'], 
                              capture_output=True, text=True, timeout=30)
        return result.returncode == 0 and '[ ]' not in result.stdout
        
    def test_superuser(self):
        """Тест наличия суперпользователя"""
        result = subprocess.run(['python3', 'manage.py', 'shell', '-c', 
                              'from django.contrib.auth.models import User; '
                              'print(User.objects.filter(is_superuser=True).exists())'], 
                              capture_output=True, text=True, timeout=30)
        return result.returncode == 0 and 'True' in result.stdout
