# Skill: Task Manager

## Опис

Цей skill дозволяє Jin керувати завданнями через Slack команди. Jin може додавати, переглядати та завершувати задачі автоматично.

## Можливості

- **Додавання задач**: `/skill add-task <description>` - Створює нову задачу
- **Список задач**: `/skill list-tasks` - Показує всі задачі
- **Завершення задач**: `/skill complete-task <id>` - Позначає задачу як виконану
- **Статус задач**: `/skill task-status` - Показує статистику задач

## Як це працює

### Архітектура

```
Slack Message → OpenClaw Bot → Task Manager Skill → tasks.json
                                                    ↓
                                         Jin Automation (cron)
                                                    ↓
                                         Виконання задач
```

### Команди

#### 1. Додати задачу

```
/skill add-task Замінити sqlite-vss на sqlite-vec
```

**Результат:**
```json
{
  "id": "2",
  "title": "Замінити sqlite-vss на sqlite-vec",
  "status": "pending",
  "created_at": "2026-02-27T11:30:00Z"
}
```

#### 2. Список задач

```
/skill list-tasks
```

**Результат:**
```
📋 Задачі:

[1] Замінити sqlite-vss на sqlite-vec - pending
[2] Оновити документацію - completed
[3] Додати нову модель - pending
```

#### 3. Завершити задачу

```
/skill complete-task 1
```

**Результат:**
```
✅ Задача #1 "Замінити sqlite-vss на sqlite-vec" завершена!
```

## Автоматизація

### Перевірка кожні 30 хвилин

Система автоматично:
1. Перевіряє Slack на нові повідомлення/згадки
2. Читає список незавершених задач з `tasks.json`
3. Виконує кожну задачу через Jin
4. Оновлює статус після виконання

### Cron Job

```bash
# Встановлюється через setup_cron.sh
*/30 * * * * /root/.openclaw/check_tasks.sh >> /var/log/jin_tasks.log 2>&1
```

## Формат tasks.json

```json
{
  "tasks": [
    {
      "id": "1",
      "title": "Замінити sqlite-vss на sqlite-vec",
      "status": "pending",
      "created_at": "2026-02-27T10:00:00Z",
      "completed_at": null
    }
  ],
  "last_updated": "2026-02-27T11:20:00Z"
}
```

## API Endpoints

### POST /api/check-chat

Викликається cron job для:
- Перевірки Slack повідомлень
- Виконання незавершених задач
- Оновлення статусу задач

### GET /api/check-chat

Повертає:
- Список всіх задач
- Кількість pending/completed задач
- Час останнього оновлення

## Логування

- **Log file**: `/var/log/jin_tasks.log`
- **Log format**: `[YYYY-MM-DD HH:MM:SS] MESSAGE`

## Приклади використання

### Сценарій 1: Користувач просить виконати завдання

```
User: Jin, будь ласка, заміни sqlite-vss на sqlite-vec в проекті
Jin: Додаю задачу до списку...
→ /skill add-task Замінити sqlite-vss на sqlite-vec
✅ Задача #1 "Замінити sqlite-vss на sqlite-vec" додана!
```

### Сценарій 2: Автоматичне виконання

```
[Cron job запускається кожні 30 хвилин]

1. Перевіряю Slack...
2. Нових повідомлень немає
3. Перевіряю задачі...
4. Знайдено 1 pending задачу
5. Виконую: Замінити sqlite-vss на sqlite-vec
6. ✅ Задача #1 виконана!
```

### Сценарій 3: Перевірка статусу

```
User: Jin, які в мене є задачі?
Jin: 
📋 Поточні задачі:

🔄 В процесі (1):
   - Замінити sqlite-vss на sqlite-vec

✅ Завершено (5):
   - Оновити документацію
   - Додати нову модель
   - ...
```

## Інтеграція з Jin

Jin автоматично використовує цей skill коли:

1. Користувач просить виконати завдання
2. В чаті є згадки про нові задачі
3. Cron job викликає `/api/check-chat`

## Безпека

- API endpoint захищений токеном `CRON_SECRET`
- Slack токени зберігаються в змінних середовища
- Файли задач зберігаються в захищеній директорії

## Версія

- Version: 1.0.0
- For: Jin (Main Agent)
- Created: 2026-02-27
