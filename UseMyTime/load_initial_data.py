#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model

User = get_user_model()

# Check if data already loaded
if User.objects.count() == 0:
    print("Loading initial data from backup...")
    try:
        call_command('loaddata', '../data_backup.json', ignorenonexistent=True)
        print(f"Data loaded successfully! Total users: {User.objects.count()}")
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)
else:
    print(f"Data already exists. Total users: {User.objects.count()}")
