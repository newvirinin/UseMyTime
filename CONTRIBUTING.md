# Вклад в проект UseMyTime

Мы рады вашему вкладу в проект UseMyTime! Этот документ поможет вам начать работу.

## Как начать

### Требования
- Python 3.8+
- Git
- Базовое знание Django и JavaScript

### Шаги для начала работы

1. **Fork репозитория**
   - Нажмите кнопку "Fork" на странице проекта
   - Склонируйте ваш fork:
   ```bash
   git clone https://gitlab.com/your-username/usemytime.git
   cd usemytime
   ```

2. **Настройка окружения**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Настройка переменных окружения**
   ```bash
   cp UseMyTime/.env.example UseMyTime/.env
   # Отредактируйте .env файл
   ```

4. **Применение миграций**
   ```bash
   python UseMyTime/manage.py migrate
   python UseMyTime/manage.py createsuperuser
   ```

5. **Запуск сервера**
   ```bash
   python UseMyTime/manage.py runserver
   ```

## Процесс разработки

### Ветка разработки
- Основная ветка: `main`
- Ветка для разработки: `develop`
- Фичи: `feature/название-фичи`
- Багфиксы: `bugfix/описание-бага`

### Создание новой фичи

1. Создайте новую ветку:
   ```bash
   git checkout -b feature/awesome-feature
   ```

2. Вносите изменения:
   - Следуйте стандартам кода PEP 8
   - Пишите тесты для новой функциональности
   - Обновляйте документацию

3. Тестируйте:
   ```bash
   python UseMyTime/manage.py test
   python UseMyTime/manage.py check
   ```

4. Коммиты:
   ```bash
   git add .
   git commit -m "feat: add awesome feature"
   ```

5. Push и Merge Request:
   ```bash
   git push origin feature/awesome-feature
   ```
   Создайте Merge Request в GitLab

### Стандарты кода

#### Python/Django
- Следуйте PEP 8
- Используйте descriptive имена переменных
- Документируйте сложные функции
- Максимальная длина строки: 88 символов

#### JavaScript
- Используйте ES6+ синтаксис
- Документируйте функции
- Избегайте глобальных переменных

#### HTML/CSS
- Используйте Bootstrap классы
- Семантическая HTML разметка
- Адаптивный дизайн

### Тестирование

- Пишите unit тесты для новых функций
- Тестируйте формы и представления
- Покрытие кода должно быть > 80%
- Используйте описательные имена тестов

### Документация

- Обновляйте README.md при добавлении новой функциональности
- Добавляйте комментарии к сложному коду
- Обновляйте CHANGELOG.md

## Pull Request Process

### Перед созданием PR
- Убедитесь, что все тесты проходят
- Проверьте код на соответствие стандартам
- Обновите документацию
- Перепроверьте, что ветка обновлена с develop

### Структура PR
- Используйте понятный заголовок
- Опишите изменения в описании
- Добавьте скриншоты, если применимо
- Свяжите с Issue, если существует

### Code Review
- Все PR должны быть проверены
- Будьте конструктивны в отзывах
- Обсуждайте изменения, а не людей
- Исправляйте замечания promptly

## Выпуск версий

### Версионирование
Используем Semantic Versioning (SemVer):
- MAJOR.MINOR.PATCH
- MAJOR: несовместимые изменения
- MINOR: новая функциональность
- PATCH: багфиксы

### Процесс выпуска
1. Обновите версию в settings.py
2. Обновите CHANGELOG.md
3. Создайте тег:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

## Сообщество

### Каналы связи
- GitLab Issues: для багов и фич
- GitLab Discussions: для вопросов
- Email: для конфиденциальных вопросов

### Поведение
- Будьте уважительны
- Помогайте другим
- Следуйте Code of Conduct

## Частые вопросы

### Q: Как добавить новую модель?
A: Создайте модель в models.py, создайте миграции, добавьте в admin.py, напишите тесты.

### Q: Как добавить новую страницу?
A: Создайте view в views.py, добавьте URL в urls.py, создайте template, добавьте тесты.

### Q: Как стилизовать компонент?
A: Используйте Bootstrap классы, добавьте custom CSS в static/css/style.css.

## Благодарности

Спасибо всем, кто вносит вклад в проект!

## Лицензия

Проект распространяется под лицензией MIT.
