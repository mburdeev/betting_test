# Простая система ставок. Тестовое задание
### Запуск приложения
```
docker-compose up -d --build
```

После запуска можно открыть документацию:
 - line-provider: http://127.0.0.1:8080/docs
 - bet-maker: http://127.0.0.1:8081/docs

### Запуск тестов
```
# line-provier
docker-compose run --entrypoint pytest line-provider
# bet-maker
docker-compose run --entrypoint pytest bet-maker
```

### Какие технологии использовал

Для решения задачи я использовал `FastAPI`, `Python3.10`. Асинхронное взаимодействие между сервисами `line-provider` и `bet-maker` реализовано с помощью очереди `RabbitMQ`, библиотека `aio-pika`. В качестве хранилища для сервиса `bet-maker` использовал `PostgreSQL`.

#### Коментарии по реализации

### line-provider

За основу взял сервис, которые был в ТЗ. Отдельно хочу отметить такие правки:

 - Разделил создание и редактирование событий на методы POST и PUT, таже добавил PATCH для отдельного редактирования статуса и коэффициента.
  - В качестве id для события взял UUID4.
 - Добавил фильтрацию не только по дедлайну, но и статусу. По моему логично, что на событие с известных исходом уже нельзя сделать ставку.
 - При редактировании добавил проверку - коэффициент и дедлайн можно изменить только у события со статусом NEW.
 - Добавил проверку коэффициента события на уровне pydantic схемы.

### bet-maker
Этот сервис я писал в более привычном для себя формате и по нему вы можете оценить мой подход к написанию FastAPI приложений. Есть деление на тематические части:
 - schemas - схемы для создания, редактирования и возврата данных
 - db - настройки подключения к БД, модели
 - services - запросы в БД, бизнес логика
 - эндпоинты поместил в app.main
Я не стал делать .env файл для более простого запуска приложения. Обычно все приватные настройки я вношу туда.

На свое предусмотрение я реализовал такую логику обновления данных о событиях:
1. Приходят данные из очереди, парсим их
2. Проверяем есть ли уже в БД такое событие
3. Если такого события нет, то сохраняем в базе
3. Если есть, то проверяем статус, мы можем менять только события где исход еще неизвестен
4. Если событие в базе NEW и нам пришло это же событие со статусом NEW, то обновляем остальные реквизиты события в БД(коэффициент, дедлайн)
5. Если событие в базе NEW, а нам пришло событие с известным исходом, то обновляем событие в базе и обновляем все ставки для этого события, изменяя статус ставки в зависмости от статуса события

Если говорить в целом о решении, то у моей реализации есть заметные слабые стороны, готов с вами их обсудить :)
