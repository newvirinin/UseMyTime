# Деплой проекта UseMyTime на Railway

## Подготовка проекта

Проект уже настроен для деплоя на Railway. Все необходимые файлы созданы:
- `railway.toml` - конфигурация Railway
- `nixpacks.toml` - конфигурация сборки
- `Procfile` - команды запуска
- `requirements.txt` - зависимости Python
- Обновлен `settings.py` для работы с переменными окружения

## Шаги деплоя

### 1. Создайте аккаунт на Railway
- Перейдите на https://railway.app
- Зарегистрируйтесь через GitHub

### 2. Создайте новый проект
- Нажмите "New Project"
- Выберите "Deploy from GitHub repo"
- Выберите ваш репозиторий UseMyTime

### 3. Добавьте PostgreSQL базу данных
- В проекте нажмите "New" → "Database" → "Add PostgreSQL"
- Railway автоматически создаст переменные окружения для подключения

### 4. Настройте переменные окружения
В разделе "Variables" добавьте:

```
SECRET_KEY=your-secret-key-here-generate-new-one
DEBUG=False
DB_ENGINE=postgresql
ALLOWED_HOSTS=your-app-name.up.railway.app
CSRF_TRUSTED_ORIGINS=https://your-app-name.up.railway.app
```

Railway автоматически добавит переменные для PostgreSQL:
- `DATABASE_URL` (Railway автоматически)
- Или используйте отдельные переменные:
  - `DB_NAME`
  - `DB_USER`
  - `DB_PASSWORD`
  - `DB_HOST`
  - `DB_PORT`

### 5. Настройте подключение к базе данных

Если Railway предоставляет `DATABASE_URL`, обновите `settings.py`:

```python
import dj_database_url

# В DATABASES добавьте:
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )
```

И добавьте в `requirements.txt`:
```
dj-database-url==2.1.0
```

### 6. Деплой
- Railway автоматически начнет деплой после коммита
- Следите за логами в разделе "Deployments"

### 7. Выполните миграции (если нужно вручную)
В Railway CLI или через веб-интерфейс:
```bash
railway run python UseMyTime/manage.py migrate
railway run python UseMyTime/manage.py createsuperuser
```

### 8. Настройте домен
- В разделе "Settings" → "Domains"
- Railway предоставит домен вида: `your-app.up.railway.app`
- Можете добавить свой кастомный домен

## Проверка деплоя

1. Откройте URL вашего приложения
2. Проверьте, что статические файлы загружаются
3. Попробуйте войти в админку: `https://your-app.up.railway.app/admin/`

## Troubleshooting

### Ошибка со статическими файлами
```bash
railway run python UseMyTime/manage.py collectstatic --no-input
```

### Ошибка с миграциями
```bash
railway run python UseMyTime/manage.py migrate
```

### Просмотр логов
```bash
railway logs
```

## Полезные команды Railway CLI

Установка CLI:
```bash
npm i -g @railway/cli
```

Вход:
```bash
railway login
```

Подключение к проекту:
```bash
railway link
```

Просмотр переменных:
```bash
railway variables
```

Запуск команд:
```bash
railway run python UseMyTime/manage.py <command>
```

## Автоматический деплой

Railway автоматически деплоит при каждом push в главную ветку GitHub.
Для отключения автодеплоя:
- Settings → "Deploy Triggers" → отключите нужную ветку

## Мониторинг

- Логи: вкладка "Deployments" → выберите деплой → "View Logs"
- Метрики: вкладка "Metrics" (CPU, Memory, Network)
- Алерты: настройте в разделе "Settings" → "Alerts"

## Стоимость

Railway предоставляет:
- $5 бесплатных кредитов в месяц
- После этого оплата по факту использования
- Примерная стоимость для небольшого Django проекта: $5-10/месяц
