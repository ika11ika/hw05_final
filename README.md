## Cоциальная сеть для публикации постов Yatube

Классическое Django-приложение структуры MVT. Настроены пагинация, кэширование, регистрация, авторизация, подписки на авторов. Написаны тесты, проверяющие работу различных компонентов приложения.


### Технологии:
Python 3.7, Django 3.2, SQLite3, pytest

### Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:

```
https://github.com/ika11ika/hw05_final.git
```

```
cd hw05_final
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python manage.py migrate
```

Запустить проект:

```
python manage.py runserver
```

