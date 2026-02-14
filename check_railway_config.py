#!/usr/bin/env python
"""
Скрипт для проверки конфигурации Railway перед деплоем
"""
import os
import sys

def check_env_var(name, required=True):
    value = os.getenv(name)
    if value:
        # Скрываем чувствительные данные
        if 'PASSWORD' in name or 'SECRET' in name:
            display_value = '***' + value[-4:] if len(value) > 4 else '***'
        else:
            display_value = value
        print(f"✅ {name} = {display_value}")
        return True
    else:
        if required:
            print(f"❌ {name} - НЕ УСТАНОВЛЕНА (обязательная)")
            return False
        else:
            print(f"⚠️  {name} - не установлена (опциональная)")
            return True

def main():
    print("=" * 60)
    print("Проверка конфигурации Railway для UseMyTime")
    print("=" * 60)
    print()
    
    all_ok = True
    
    print("🔐 Django настройки:")
    all_ok &= check_env_var('SECRET_KEY', required=True)
    all_ok &= check_env_var('DEBUG', required=False)
    all_ok &= check_env_var('ALLOWED_HOSTS', required=False)
    all_ok &= check_env_var('CSRF_TRUSTED_ORIGINS', required=False)
    print()
    
    print("🗄️  База данных:")
    all_ok &= check_env_var('DB_ENGINE', required=True)
    all_ok &= check_env_var('DB_HOST', required=True)
    all_ok &= check_env_var('DB_PORT', required=True)
    all_ok &= check_env_var('DB_NAME', required=True)
    all_ok &= check_env_var('DB_USER', required=True)
    all_ok &= check_env_var('DB_PASSWORD', required=True)
    print()
    
    print("📧 Email (опционально):")
    check_env_var('EMAIL_HOST', required=False)
    check_env_var('EMAIL_HOST_USER', required=False)
    check_env_var('EMAIL_HOST_PASSWORD', required=False)
    print()
    
    print("🌐 Railway переменные:")
    check_env_var('PORT', required=False)
    check_env_var('RAILWAY_ENVIRONMENT', required=False)
    print()
    
    print("=" * 60)
    if all_ok:
        print("✅ Все обязательные переменные настроены!")
        print("=" * 60)
        return 0
    else:
        print("❌ Некоторые обязательные переменные не настроены!")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
