# Деплой KVER на PythonAnywhere (бесплатный тариф)

Проект уже подготовлен: `python-decouple`, `STATIC_ROOT`, `MEDIA_ROOT`, `requirements.txt`.

## 1. Перед загрузкой (локально)

### Проверка настроек

1. Скопируйте `.env.example` → `.env` (для локальной работы).
2. Сгенерируйте секретный ключ для **продакшена** (сохраните — понадобится на хостинге):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

3. Убедитесь, что проект запускается:

```bash
python manage.py check
python manage.py migrate
```

### Что загружать на хостинг

Загрузите **весь проект**, кроме того, что в `.gitignore`:

- не загружайте `.venv/`, `.env`, `__pycache__/`, `staticfiles/` (соберёте на сервере)
- **базу** `db.sqlite3` — загрузите отдельно, если нужны ваши тестовые пользователи; иначе создайте на сервере через `migrate` + `createsuperuser`

Удобно: GitHub + `git clone` на PythonAnywhere (вкладка Consoles → Bash).

---

## 2. Регистрация на [pythonanywhere.com](https://www.pythonanywhere.com)

Бесплатный аккаунт: домен вида `https://ВАШЛОГИН.pythonanywhere.com`.

---

## 3. Установка на сервере (Bash-консоль)

```bash
cd ~
git clone https://github.com/ВАШ_РЕПО/KVER.git
# или загрузите файлы через Files → Upload

cd KVER
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

---

## 4. Переменные окружения

**Web** → ваш сайт → **Environment variables** (или секция в конфиге WSGI):

| Переменная | Значение (пример) |
|------------|-------------------|
| `SECRET_KEY` | ваш случайный ключ |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `вашлогин.pythonanywhere.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://вашлогин.pythonanywhere.com` |
| `YOUTUBE_API_KEY` | по желанию |

---

## 5. Web-приложение

**Web** → **Add a new web app** → Manual configuration → Python 3.10.

### WSGI-файл

Откройте WSGI configuration и укажите (подставьте свой логин и путь):

```python
import os
import sys

path = '/home/ВАШЛОГИН/KVER'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ.setdefault('SECRET_KEY', 'ваш-ключ')
os.environ.setdefault('DEBUG', 'False')
os.environ.setdefault('ALLOWED_HOSTS', 'ВАШЛОГИН.pythonanywhere.com')
os.environ.setdefault('CSRF_TRUSTED_ORIGINS', 'https://ВАШЛОГИН.pythonanywhere.com')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

*(Переменные лучше задать в Environment variables панели, а не дублировать в WSGI.)*

### Virtualenv

**Web** → Virtualenv: `/home/ВАШЛОГИН/KVER/venv`

### Статика

**Web** → Static files:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/ВАШЛОГИН/KVER/staticfiles` |

### Медиа (фото профилей, каверы)

| URL | Directory |
|-----|-----------|
| `/media/` | `/home/ВАШЛОГИН/KVER/media` |

Создайте папку `media`, если её нет: `mkdir -p ~/KVER/media`

---

## 6. Перезапуск

**Web** → зелёная кнопка **Reload**.

Откройте `https://ВАШЛОГИН.pythonanywhere.com`.

---

## 7. Частые проблемы

| Симптом | Решение |
|---------|---------|
| DisallowedHost | Проверьте `ALLOWED_HOSTS` |
| 403 CSRF | Добавьте `CSRF_TRUSTED_ORIGINS` с `https://` |
| Стили не грузятся | `collectstatic` + mapping `/static/` → `staticfiles` |
| Фото не открываются | mapping `/media/` → `media` |
| 500 ошибка | **Web** → Error log; локально проверьте с `DEBUG=False` |
| SQLite readonly | Файл `db.sqlite3` должен лежать в проекте с правами на запись |

---

## 8. Обновление после изменений в коде

```bash
cd ~/KVER
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Затем **Reload** на вкладке Web.

---

## Альтернативы

- **Render / Railway** — есть PostgreSQL, но настройка сложнее.
- Для диплома и теста с друзьями **PythonAnywhere + SQLite** обычно достаточно.
