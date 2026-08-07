# FullCRM Platform

FullCRM — модульная B2B CRM-платформа: сделки и контакты, коммуникации, аналитика воронки и ИИ-рекомендации.  
Архитектура рассчитана на подключение модулей по организации без переписывания ядра.

**Демо / prod:** `https://testfullcrm.alexklyvibe.ru`

**Документация для администратора:**
- [Руководство администратора](./Руководство%20администратора.docx) (Word)
- Исходник в Markdown: [userAdminSetup.md](./userAdminSetup.md)

---

## Стек

| Слой | Технологии |
|------|------------|
| Web | Next.js 15 (App Router), React 19, TypeScript, Tailwind |
| API | FastAPI, SQLAlchemy, Alembic, PyJWT |
| БД | PostgreSQL 16 |
| Инфра | Docker Compose, Nginx; Redis зарезервирован под фоновые задачи |
| ИИ | OpenAI Chat Completions (`AI_MODEL` / `OPENAI_MODEL`, по умолчанию `gpt-4o-mini`) |

Web ходит в API через same-origin BFF (`/api/*`). Данные UI CRM живут в PostgreSQL, не в статических JSON портфолио.

---

## Что умеет платформа сейчас

### 1. Авторизация и мультитенантность

- Вход по email/password, JWT в httpOnly cookies (access + refresh)
- Организации, роли, permissions (`crm.*`, `communications.*`, `ai.read`, `analytics.read`, `admin.manage`)
- Профиль `/auth/me`: пользователь, орг, роли, права, **включённые модули**
- Настройки организации (admin): пороги аналитики, тогглы модулей, статусы интеграций

### 2. Модуль CRM (базовый, всегда включён)

- Компании, контакты, сделки (CRUD)
- Воронка: этапы New → Qualified → Won (в UI: Новая / Квалифицирована / Завершена)
- **Kanban на `/crm/deals`**: перетаскивание сделок между колонками этапов (`POST /deals/{id}/transition`); вид «Список» сохранён
- Переходы этапов, события (EventLog), ответственные
- На карточке компании: связанные контакты и сделки со статусами и ссылками
- Telegram Chat ID на контакте (`meta.telegram_chat_id`) для матчинга входящих

**Страницы:** `/crm`, `/crm/companies`, `/crm/contacts`, `/crm/deals`

### 3. Модуль «Коммуникации»

- Timeline сообщений на карточке контакта/сделки
- Ручные записи канала `email`
- Статусы интеграций: Telegram / Gmail / Calendar
- Poll Telegram: `POST /communications/telegram/poll` (кнопка в Настройки → Интеграции)

**Страница:** `/communications`

### 4. Модуль «Аналитика»

- Сводка воронки: сделки по этапам, конверсия, активность
- Деньги: сумма открытых / завершённых, средний чек
- Средний цикл закрытия (по won)
- Просроченные сделки (порог из настроек) — клик ведёт в карточку сделки
- Воронка с полосками (count + сумма по этапу)
- Отдельная страница `/analytics` + виджет на Обзоре
- Пороги: `stale_deal_days`, `activity_window_days` (Настройки → Аналитика)

### 5. Модуль «ИИ»

Нет отдельного пункта сайдбара — работает внутри CRM и Аналитики.

**На карточке сделки** (`/crm/deals/{id}`):
- вероятность закрытия, следующее действие, черновик сообщения
- контекст: сделка, коммуникации, события, история сделок компании
- роль: сильный бизнес-аналитик / sales ops

**На странице аналитики** (`/analytics`):
- кнопка «Получить рекомендации»
- здоровье коммерции, перспективы, 3–5 рекомендаций, план на 1–2 недели и месяц
- контекст: сводка analytics + топ открытых + просроченные

**Режимы:**
| Режим | Когда |
|-------|--------|
| Демо (mock) | `AI_MOCK=true` или нет ключа |
| Подключён (live) | `AI_MOCK=false` + `OPENAI_API_KEY` |
| Ограничен (degraded) | live упал → fallback на mock |

Модель задаётся env: `AI_MODEL` или alias `OPENAI_MODEL`.

### 6. Настройки организации (`admin.manage`)

`/settings` — вкладки:
- **Аналитика** — пороги stale / activity window
- **Интеграции** — статусы каналов + Poll Telegram
- **Модули** — включение/выключение (CRM нельзя отключить)

---

## Как подключаются модули

### Принцип

1. В БД таблица `module_toggles` (ключ модуля + `enabled`) per organization  
2. В сессии пользователя — только включённые модули  
3. API: `require_module("…")` → 403, если модуль выключен  
4. UI: `hasModule` — скрывает страницы/панели; сайдбар показывает пункты включённых модулей  
5. Права отдельно: даже при включённом модуле нужен permission (`ai.read`, `analytics.read`, …)

### Управление

**UI:** Настройки → Модули (нужен `admin.manage`)  
**API:**
- `GET /organizations/me/modules`
- `PATCH /organizations/me/modules` — тело `{ "modules": [{ "module_key": "ai", "enabled": true }] }`

Ключи сейчас: `crm` | `communications` | `ai` | `analytics`

### Env для «живых» интеграций

```env
# ИИ
OPENAI_API_KEY=sk-...
AI_MOCK=false
AI_MODEL=gpt-4o-mini          # или OPENAI_MODEL=...

# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ENABLED=true
TELEGRAM_POLL_COOLDOWN_SECONDS=30
```

Gmail и Calendar в MVP — stub (OAuth не подключён).

---

## Карта страниц

| URL | Назначение |
|-----|------------|
| `/dashboard` | Обзор, виджет аналитики |
| `/crm/...` | Компании, контакты, сделки |
| `/communications` | Интеграции / коммуникации |
| `/analytics` | Полная аналитика + ИИ-рекомендации по бизнесу |
| `/settings` | Аналитика / Интеграции / Модули |

---

## Локальный запуск

**Web:**

```powershell
cd apps/web
npm install
npm run dev
```

**API:**

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Health:
- `GET http://localhost:8000/health`
- `GET http://localhost:8000/health/ready`

Demo seed (только local/dev):

```powershell
$env:SEED_DEMO="true"
$env:SEED_ADMIN_PASSWORD="your-password"
python -m app.db.seed
```

**Prod compose:** `docker compose -f docker-compose.prod.yml up -d --build`  
Секреты — только в `.env` (шаблон `.env.example` / `.env.prod.example`). Не коммитить ключи.

Маршрутизация prod: `/` → web, `/api/` → FastAPI, `/health` → API.

---

## Перспективы развития

### Ближайший горизонт (усиление текущего)

- Gmail / Calendar OAuth (сейчас stub)
- Очередь Telegram/AI через Redis worker (Redis уже в prod compose)
- Кэш / snapshot аналитики при росте объёма данных
- Разрез аналитики по ответственным, период vs период
- Конверсия этапа → этапа из EventLog
- Rate-limit и квоты OpenAI per org
- Admin: пользователи и роли из UI (сейчас seed/bootstrap)

### Модули, которые логично добавить

Платформа уже заточена под тогглы: новый модуль = ключ в `DEFAULT_MODULES` + permission + `require_module` + пункт UI.

| Модуль | Зачем | Что даёт |
|--------|--------|----------|
| **Tasks / Activities** | Планирование касаний | Задачи, дедлайны, напоминания, связь со сделкой |
| **Documents** | КП и договоры | Файлы, версии, шаблоны, статус согласования |
| **Billing / Invoices** | Деньги после won | Счета, оплаты, связка с суммой сделки |
| **Reports** | Кастомные отчёты | Конструктор метрик, экспорт CSV/Excel, расписание |
| **Knowledge / Playbooks** | Стандарты продаж | Скрипты, чек-листы этапов, FAQ для менеджеров |
| **Portal** | Кабинет клиента | Статус сделки, переписка, загрузка файлов |
| **Telephony** | Звонки | CDR, запись, автосоздание активности |
| **WhatsApp / Max** | Мессенджеры | Канал рядом с Telegram в communications |
| **Marketing** | Lead gen | Формы, UTM, источник лида → контакт/сделка |
| **Forecast** | Прогноз выручки | Weighted pipeline, commit/best case |
| **Audit / Compliance** | Регуляторика | Расширенный журнал, retention, экспорт аудита |
| **Workflow / Automations** | No-code правила | «Если stale > N → задача/уведомление» |
| **Multi-pipeline** | Несколько воронок | B2B / сервис / партнёры в одной орг |
| **HR / Quota** | Мотивация | Планы менеджеров, выполнение квоты |

Рекомендуемый порядок внедрения модулей:

1. **Tasks** — закрывает операционный gap follow-up  
2. **Documents** — нужен почти любому B2B-заказчику  
3. **Gmail live + Automations** — связка коммуникаций и дисциплины  
4. **Reports / Forecast** — апгрейд аналитики до управленческой  
5. **Billing** — если сценарий «от сделки к деньгам»

### Масштабирование архитектуры

Уже заложено:
- module toggles per org
- RBAC permissions
- stateless API, query-time analytics
- AI provider abstraction (mock / openai / degraded)
- env-конфиг модели и интеграций

Дальше без ломки ядра:
- background workers (poll, AI batch, rollups)
- materialized analytics / Redis cache
- org-level feature flags и квоты
- отдельные read-replicas для тяжёлых отчётов

---

## Роли в продукте (типичный сценарий)

| Роль | Модули | Что делает |
|------|--------|------------|
| Admin | все + settings | включает модули, пороги, интеграции |
| Manager | CRM, Communications, AI | ведёт сделки, пишет клиентам, смотрит ИИ на сделке |
| Analyst | Analytics, AI, CRM read | смотрит `/analytics`, запрашивает org-рекомендации |

---

## Важно

- CRM — базовый модуль, отключить нельзя  
- ИИ — advisory: рекомендации справочные, не источник истины  
- Секреты только через ENV  
- Demo seed — только для local/dev (`SEED_DEMO`), не для production без явного bootstrap

---

## Лицензия / репозиторий

Исходники: GitHub `FullCRM` (см. remote репозитория).  
Вопросы по деплою: `scripts/update-prod.sh`, `docker-compose.prod.yml`.
