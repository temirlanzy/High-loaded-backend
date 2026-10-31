# To-Do / Task Tracker API

Реализация SIS #1: REST + JSON API на Python (FastAPI + SQLAlchemy).

## Запуск

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs

## Настройки (переменные окружения)

| Переменная     | По умолчанию              | Описание                                   |
|----------------|---------------------------|--------------------------------------------|
| `DATABASE_URL` | `sqlite:///./tasks.db`    | Для PostgreSQL: `postgresql+psycopg2://user:pass@host/db` |
| `JWT_SECRET`   | `change-me-in-production` | Секрет для подписи токенов                 |
| `JWT_TTL_MIN`  | `60`                      | Время жизни токена в минутах               |

## Эндпоинты

| Метод  | Путь                  | Описание                                              |
|--------|-----------------------|-------------------------------------------------------|
| POST   | `/v1/auth/register`   | Регистрация (`email`, `password` ≥ 8 символов)        |
| POST   | `/v1/auth/login`      | Вход, возвращает `access_token`                       |
| POST   | `/v1/tasks`           | Создать задачу (201). Заголовок `Idempotency-Key` — опционально |
| GET    | `/v1/tasks`           | Список своих задач (`status`, `priority`, `limit`, `offset`) |
| GET    | `/v1/tasks/{id}`      | Одна задача                                           |
| PATCH  | `/v1/tasks/{id}`      | Изменить задачу                                       |
| DELETE | `/v1/tasks/{id}`      | Удалить задачу (204)                                  |

Статусы: `todo`, `in_progress`, `done`. Приоритеты: `low`, `medium`, `high`.
Ошибки: 400 — неверные данные, 401 — нет/неверный токен, 404 — задача не найдена.

## Пример

```bash
curl -X POST localhost:8000/v1/auth/register -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","password":"password123"}'

TOKEN=$(curl -s -X POST localhost:8000/v1/auth/login -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","password":"password123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -X POST localhost:8000/v1/tasks -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Finish SIS 1","priority":"high","due_date":"2026-10-20T18:00:00Z"}'
```

## Тесты

```bash
pytest -q
```
