
### Адрес сервера - foodgramforme.ddns.net
### Админка - admin@admin.ru
### Пароль - adminparol123

# Сервис Foodgram

### _Описание_
Веб-сервис, позволяющий пользователям публиковать рецепты, подписываться друг на друга, добавлять рецепты в избранное, формировать и скачавать список необходимых ингредиентов для выбранных рецептов.

### _Установка_
Клонируйте репозиторий на свой компьютер
Находясь в главной директории (/foodgram-project-react) выполните команду:
```
docker compose -f docker-compose.production.yml up
```
Затем выполните миграции, соберите статику, создайте суперпользовтаеля и загрузите данные из базы
```
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py load_data
```
