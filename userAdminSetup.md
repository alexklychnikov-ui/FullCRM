# Инструкция администратора FullCRM

Документ для администратора организации: первичный вход, люди и роли, модули, аналитика и интеграции.

**Права:** нужен permission `admin.manage` (роль admin после seed/bootstrap).

**Prod (пример):** https://testfullcrm.alexklyvibe.ru  
**Настройки:** https://testfullcrm.alexklyvibe.ru/settings

Локально URL замените на свой `WEB_URL` (обычно `http://localhost:3000`).

---

## 1. Первый вход

1. Откройте `/login`.
2. Войдите учётной записью администратора (после prod bootstrap или demo seed).
3. В сайдбаре должен быть пункт **Настройки**.
4. Если пункта нет — у пользователя нет `admin.manage`. Обратитесь к тому, кто поднимал сервер / bootstrap.

После входа проверьте:

| Раздел | URL |
|--------|-----|
| Обзор | `/dashboard` |
| Настройки / Люди | `/settings` или `/settings?tab=users` |
| Модули | `/settings?tab=modules` |
| Интеграции | `/settings?tab=integrations` |
| Аналитика (пороги) | `/settings?tab=analytics` |

---

## 1.1. Люди и роли (создать менеджера / выдать роль / отозвать доступ)

**Где:** Настройки → **Люди** (вкладка по умолчанию)  
**URL:** https://testfullcrm.alexklyvibe.ru/settings?tab=users  
**Права:** только с `admin.manage`.

Роли `admin` / `manager` / `analyst` создаются в организации автоматически при первом открытии этого раздела (или вызове API).

### Создать менеджера

1. Откройте **Настройки → Люди**.
2. В блоке **Создать пользователя** заполните:
   - **Email** — логин (уникален в организации);
   - **ФИО**;
   - **Пароль** — не короче 8 символов;
   - **Роли** — отметьте `manager` (можно несколько ролей сразу).
3. Нажмите **Создать**.
4. Передайте сотруднику email и пароль; он входит через `/login`.

Типичный сценарий: один `admin` (вы) + несколько `manager` для продаж.

### Выдать или сменить роль

1. В списке пользователей найдите нужного человека.
2. Отметьте/снимите чекбоксы ролей (`admin`, `manager`, `analyst`).
3. Нажмите **Сохранить роли**.

Права применяются при следующем запросе/обновлении сессии (после перелогина права точно совпадут с ролями).

| Роль | Что может |
|------|-----------|
| `admin` | всё + Настройки (`admin.manage`): люди, модули, пороги, интеграции |
| `manager` | CRM (чтение/запись), коммуникации, AI и analytics read — **без** админки |
| `analyst` | чтение CRM и коммуникаций + AI/analytics — без записи CRM и без админки |

### Отозвать доступ

1. У пользователя нажмите **Отозвать доступ**.
2. Учётная запись становится неактивной: вход и refresh-сессии блокируются, активные сессии сбрасываются.
3. Чтобы вернуть: **Восстановить доступ** (пароль тот же, пока не смените отдельно через API/админа).

### Ограничения

- Нельзя отозвать доступ **у себя**.
- Нельзя оставить организацию **без активного** пользователя с ролью `admin`.
- Нельзя снять роль `admin` у последнего активного администратора.

### API (для автоматизации)

Все эндпоинты требуют `admin.manage`, scope — своя организация:

| Метод | Путь | Назначение |
|-------|------|------------|
| `GET` | `/organizations/me/users` | список пользователей |
| `POST` | `/organizations/me/users` | создать (`email`, `full_name`, `password`, `roles[]`) |
| `PATCH` | `/organizations/me/users/{id}` | `is_active`, `full_name`, `password` |
| `PUT` | `/organizations/me/users/{id}/roles` | заменить набор ролей |
| `GET` | `/organizations/me/roles` | каталог ролей орг |

---

## 2. Модули организации

**Где:** Настройки → **Модули**  
**URL:** `/settings?tab=modules`

Включайте/выключайте модули для всей организации и нажмите **Сохранить модули**.

| Модуль | Ключ | Что появляется |
|--------|------|----------------|
| CRM | `crm` | Компании, контакты, сделки, воронка. **Нельзя отключить** |
| Коммуникации | `communications` | `/communications`, timeline на карточках, статусы интеграций |
| Аналитика | `analytics` | `/analytics`, виджет на Обзоре |
| ИИ | `ai` | Панели «Получить рекомендации» на сделке и в аналитике |

**Важно:**

- Выключенный модуль → API отдаёт 403, UI скрывает раздел.
- ИИ на странице аналитики требует **оба** модуля: `analytics` + `ai`.
- Права (`ai.read`, `analytics.read`, …) задаются ролями отдельно от тогглов.

Рекомендуемый стартовый набор для демо: все четыре модуля включены.

---

## 3. Аналитика (пороги)

**Где:** Настройки → **Аналитика**  
**URL:** `/settings?tab=analytics`

| Параметр | Смысл | Default |
|----------|--------|---------|
| Дней без обновления сделки | Сделки `open` старше порога попадают в «просроченные» | 7 |
| Окно активности (дней) | Счётчик событий за последние N дней | 7 |

Сохраните → обновите `/analytics` или Обзор.

Связанные страницы:

- https://testfullcrm.alexklyvibe.ru/analytics  
- https://testfullcrm.alexklyvibe.ru/dashboard  

---

## 4. Интеграции — обзор

**Где:** Настройки → **Интеграции**  
**URL:** `/settings?tab=integrations`

Также статусы видны на `/communications`.

| Канал | Статус в MVP | Где настраивается |
|-------|--------------|-------------------|
| Telegram | live / stub / disabled | ENV на сервере + Poll в UI |
| Gmail | stub | OAuth пока нет |
| Calendar | stub | OAuth пока нет |
| OpenAI (ИИ) | mock / live / degraded | ENV на сервере |

Ниже — отдельный блок по каждой интеграции.

---

## 5. Telegram

### 5.1. Что умеет

- Опрос входящих сообщений бота (`getUpdates`)
- Привязка к контакту по полю **Telegram Chat ID**
- Создание записи в communications + событие в CRM
- Кнопка **Опрос Telegram** в Настройки → Интеграции

Ручная отправка «как из Telegram» через форму сообщений **запрещена** — только poll.

### 5.2. Создание бота (веб)

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)  
   Веб-клиент: https://web.telegram.org/  
2. Команда `/newbot` → имя и username бота.  
3. Скопируйте **HTTP API token** (вид `123456:ABC-DEF...`).  
4. Документация Bot API: https://core.telegram.org/bots/api  
5. Метод обновлений: https://core.telegram.org/bots/api#getupdates  

Проверка токена (подставьте свой token):

```text
https://api.telegram.org/bot<TOKEN>/getMe
```

### 5.3. ENV на сервере (обязательно)

В `.env` API / Docker Compose:

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_ENABLED=true
TELEGRAM_POLL_COOLDOWN_SECONDS=30
```

| Переменная | Значение |
|------------|----------|
| `TELEGRAM_BOT_TOKEN` | токен от BotFather |
| `TELEGRAM_ENABLED` | `true` для live |
| `TELEGRAM_POLL_COOLDOWN_SECONDS` | пауза между poll (сек), default 30 |

После изменения `.env` пересоздайте/перезапустите контейнер `api`.

### 5.4. Режимы статуса

| Режим | Условие |
|-------|---------|
| **Подключён (live)** | токен задан + `TELEGRAM_ENABLED=true` |
| **Отключён** | токен задан, но `TELEGRAM_ENABLED=false` |
| **Заглушка (stub)** | токена нет |

### 5.5. Привязка контакта

1. CRM → Контакты → карточка контакта (или создание).  
2. Поле **Telegram Chat ID** — числовой id чата с ботом (не @username).  
3. Сохраните.

Как узнать Chat ID:

1. Пользователь пишет вашему боту любое сообщение.  
2. Откройте (подставьте token):

```text
https://api.telegram.org/bot<TOKEN>/getUpdates
```

3. В JSON найдите `"chat":{"id": 123456789}` — это Chat ID.  
4. Впишите `123456789` в карточку контакта.

Сторонние helper-боты (на свой риск): [@userinfobot](https://t.me/userinfobot), [@getidsbot](https://t.me/getidsbot).

### 5.6. Опрос сообщений

1. Модуль **Коммуникации** включён.  
2. У пользователя есть `communications.write` (у admin обычно есть).  
3. Настройки → Интеграции → **Опрос Telegram**.  
4. Сообщения с известным Chat ID появятся в timeline контакта/сделки.

Если кнопка неактивна — статус Telegram не `live` (проверьте ENV).

Cooldownoldown: повторный poll раньше `TELEGRAM_POLL_COOLDOWN_SECONDS` будет отклонён.

### 5.7. Чеклист Telegram

- [ ] Бот создан в BotFather  
- [ ] `TELEGRAM_BOT_TOKEN` + `TELEGRAM_ENABLED=true` в prod `.env`  
- [ ] API перезапущен  
- [ ] В UI статус «Подключён»  
- [ ] У контактов заполнен Telegram Chat ID  
- [ ] Пользователь написал боту  
- [ ] Poll создал сообщения в CRM  

---

## 6. OpenAI (модуль ИИ)

### 6.1. Что умеет

- Рекомендации на карточке сделки: вероятность, next step, черновик  
- Рекомендации на `/analytics`: здоровье бизнеса, перспективы, план  
- Режимы: mock / live / degraded  

### 6.2. Получение ключа (веб)

1. Зарегистрируйтесь / войдите: https://platform.openai.com/  
2. API keys: https://platform.openai.com/api-keys  
3. Создайте ключ (`sk-...`), сохраните вне git.  
4. Биллинг / лимиты: https://platform.openai.com/settings/organization/billing  
5. Модели: https://platform.openai.com/docs/models  

### 6.3. ENV на сервере

```env
OPENAI_API_KEY=sk-...
AI_MOCK=false
AI_MODEL=gpt-4o-mini
# или алиас:
# OPENAI_MODEL=gpt-4o-mini
```

| Переменная | Смысл |
|------------|--------|
| `OPENAI_API_KEY` | ключ OpenAI |
| `AI_MOCK` | `true` = демо без API; `false` = live |
| `AI_MODEL` / `OPENAI_MODEL` | имя модели (приоритет у `AI_MODEL`) |

После правки `.env` — перезапуск `api`.

### 6.4. Включение в UI

1. Настройки → Модули → **ИИ** включён → Сохранить.  
2. Для org-рекомендаций также включите **Аналитика**.  
3. Откройте сделку → «Получить рекомендации».  
4. Или `/analytics` → «Получить рекомендации».  

Badge: **Подключён** = live, **Демо** = mock, **Ограничен** = ошибка API → fallback.

### 6.5. Чеклист ИИ

- [ ] Ключ создан на platform.openai.com  
- [ ] `OPENAI_API_KEY` + `AI_MOCK=false` в `.env`  
- [ ] Модель доступна аккаунту (`AI_MODEL`)  
- [ ] Модуль ИИ включён  
- [ ] На сделке /analytics кнопка отдаёт ответ на русском  

---

## 7. Gmail (stub)

### 7.1. Текущее состояние

В MVP Gmail всегда в режиме **заглушка**. OAuth не подключён.

- Статус в UI: stub  
- Ручное создание сообщений с `channel_type=gmail` — запрещено  
- Для переписки используйте канал **email** (ручная запись в timeline)  

### 7.2. Что понадобится для live (перспектива)

Когда будете подключать:

1. Google Cloud Console: https://console.cloud.google.com/  
2. Создать проект → APIs & Services → Enable **Gmail API**:  
   https://console.cloud.google.com/apis/library/gmail.googleapis.com  
3. OAuth consent screen:  
   https://console.cloud.google.com/apis/credentials/consent  
4. Credentials → OAuth 2.0 Client ID (Web application):  
   https://console.cloud.google.com/apis/credentials  
5. Authorized redirect URI — callback вашего FullCRM (будет задан при реализации).  
6. Документация Gmail API: https://developers.google.com/gmail/api/guides  

Пока достаточно знать: в UI канал виден как stub, боевой OAuth — следующий этап.

---

## 8. Календарь (stub)

### 8.1. Текущее состояние

Google Calendar в MVP — **заглушка**, синхронизация отложена.

### 8.2. Что понадобится для live (перспектива)

1. Google Cloud Console: https://console.cloud.google.com/  
2. Enable **Google Calendar API**:  
   https://console.cloud.google.com/apis/library/calendar-json.googleapis.com  
3. Тот же OAuth client / consent, что и для Gmail (часто один проект).  
4. Документация: https://developers.google.com/calendar/api/guides/overview  

В UI до реализации OAuth статус останется stub.

---

## 9. Ручной email в CRM (без Gmail OAuth)

Пока Gmail stub, переписку можно **зафиксировать вручную** в UI:

1. Модуль **Коммуникации** включён.  
2. Откройте карточку **контакта** или **сделки**.  
3. Блок **Коммуникации** → форма **«Добавить сообщение (email)»**.  
4. Выберите направление (исходящее / входящее), введите текст → **Сохранить в timeline**.  

Сообщение появится в ленте коммуникаций и в событиях CRM.  
Письмо из реального почтового ящика **не отправляется** — это запись в CRM, не SMTP/Gmail.

---

## 10. Типовой сценарий настройки «с нуля» (admin)

1. Войти под admin → `/settings` (вкладка **Люди**).  
2. **Люди:** при необходимости создать менеджера(ов) с ролью `manager`, выдать роли.  
3. **Модули:** включить Communications, Analytics, AI → Сохранить.  
4. **Аналитика:** вкладка → выставить пороги (например 7 / 7) → Сохранить.  
5. **Telegram:** BotFather → токен → `.env` → restart API → статус live.  
6. Создать/открыть контакт → указать Telegram Chat ID.  
7. Клиент пишет боту → **Опрос Telegram**.  
8. **OpenAI:** ключ → `.env` (`AI_MOCK=false`) → restart → проверка на сделке и `/analytics`.  
9. Gmail/Calendar оставить stub до отдельной задачи OAuth.  

---

## 11. Где что править (кратко)

| Задача | UI | Сервер (.env) |
|--------|----|----------------|
| Люди / роли / отзыв доступа | `/settings?tab=users` | — |
| Модули | `/settings?tab=modules` | — |
| Пороги аналитики | `/settings?tab=analytics` | — |
| Poll Telegram | `/settings?tab=integrations` | `TELEGRAM_*` |
| Chat ID контакта | `/crm/contacts/{id}` | — |
| Live ИИ | модуль AI + кнопки | `OPENAI_API_KEY`, `AI_MOCK`, `AI_MODEL` |
| Gmail / Calendar live | пока нет | позже OAuth |

Секреты **не** хранить в git и **не** вставлять в этот файл с реальными значениями.

---

## 12. Полезные ссылки (сводка)

| Сервис | Ссылка |
|--------|--------|
| FullCRM (prod) | https://testfullcrm.alexklyvibe.ru |
| Настройки / Люди | https://testfullcrm.alexklyvibe.ru/settings?tab=users |
| Аналитика (пороги) | https://testfullcrm.alexklyvibe.ru/settings?tab=analytics |
| Интеграции | https://testfullcrm.alexklyvibe.ru/settings?tab=integrations |
| Модули | https://testfullcrm.alexklyvibe.ru/settings?tab=modules |
| Аналитика продукта | https://testfullcrm.alexklyvibe.ru/analytics |
| Telegram BotFather | https://t.me/BotFather |
| Telegram Web | https://web.telegram.org/ |
| Telegram Bot API | https://core.telegram.org/bots/api |
| OpenAI Platform | https://platform.openai.com/ |
| OpenAI API keys | https://platform.openai.com/api-keys |
| Google Cloud Console | https://console.cloud.google.com/ |
| Gmail API | https://console.cloud.google.com/apis/library/gmail.googleapis.com |
| Calendar API | https://console.cloud.google.com/apis/library/calendar-json.googleapis.com |

---

*Версия инструкции соответствует MVP FullCRM: люди/роли из UI, модули CRM / Communications / Analytics / AI, интеграции Telegram (live) + Gmail/Calendar (stub).*
