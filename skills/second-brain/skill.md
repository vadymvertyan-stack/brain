# Second Brain Sync Skill

## Опис
Цей skill автоматично зберігає нотатки з кожної розмови Jin з користувачем у "другий мозок" - структуровану систему PARA + Zettelkasten для довгострокового зберігання та пошуку інформації.

## Автоматичний виклик

### Коли викликати
Цей skill повинен викликатися **після кожної завершеної розмови** з користувачем:
- Після відповіді на запит користувача
- Після виконання завдання
- Після будь-якої взаємодії, що містить корисну інформацію

### Що зберігати
- Запит користувача
- Відповідь Jin (основні ідеї, рішення, результати)
- Ключові рішення та їх обґрунтування
- Посилання на створені файли чи ресурси
- Помилки та їх вирішення (якщо були)

## Використання

### Автоматичне збереження (рекомендовано)

```bash
# Синхронізувати розмову в другий мозок
python /root/Kilo_Code/sync_to_github.py --input "CONTENT"
```

### Приклад виклику

```python
# Після відповіді користувачу
conversation_summary = """
Користувач: Як налаштувати voice library?
Jin: Налаштування voice library включає:
1. Встановлення залежностей: pip install voicebox-adapter
2. Налаштування профілю в voicebox_adapter/profile.py
3. Додавання API ключів в .env файл
4. Тестування через test_gemini.py

Деталі: Використовується voicebox адаптер з OpenAI сумісним API.
Результат: Створено конфігурацію для голосової бібліотеки.
"""

# Виклик скрипта
subprocess.run([
    'python', '/root/Kilo_Code/sync_to_github.py',
    '--input', conversation_summary,
    '--category', 'resources'
])
```

## Параметри скрипта

| Параметр | Опис | Приклад |
|----------|------|---------|
| `--input`, `-i` | Текст розмови для збереження | "Користувач запитав..." |
| `--category`, `-c` | Категорія PARA | projects, areas, resources, archives, evergreens |
| `--title`, `-t` | Заголовок нотатки | "Налаштування Voice Library" |
| `--tags`, `-tag` | Теги через кому | voice,library,setup |
| `--dry-run` | Попередній перегляд | (без збереження) |

### Автовизначення категорії
Скрипт автоматично визначає категорію на основі ключових слів:
- **projects**: project, implement, build, create, develop, task, deadline, milestone
- **areas**: responsibility, area, manage, oversee, maintain, support
- **resources**: learn, study, reference, tutorial, documentation, research, book, course
- **archives**: completed, finished, archived, inactive, old, deprecated
- **evergreens**: за замовчуванням для постійних знань

## Структура нотатки

Нотатки зберігаються у форматі:

```markdown
---
id: 202602271030-note123
title: "Налаштування Voice Library"
tags: [voice, library, setup]
date: 2026-02-27
category: 300-resources
links: []
---

# Налаштування Voice Library

## Capture
Користувач запитав про налаштування voice library...

## Organize
Основні кроки:
1. Встановлення залежностей
2. Налаштування профілю
3. Додавання API ключів

## Distill
Ключові рішення:
- Використання voicebox адаптера
- OpenAI сумісний API інтерфейс

## Express
Результат: Повна інструкція з налаштування
```

## Шляхи до файлів

```
/root/brain-second-brain/
├── 100-projects/    # Активні проекти
├── 200-areas/       # Сфери відповідальності
├── 300-resources/   # Ресурси для вивчення
├── 400-archives/    # Архівні нотатки
├── 500-evergreens/  # Постійні нотатки
└── vectors.db       # Векторна база для пошуку
```

## Векторна індексація

Після збереження нотатки вона автоматично індексується для семантичного пошуку:

```bash
# Запустити індексацію
python /root/brain-second-brain/index_to_vector.py

# Шукати нотатки
python /root/brain-second-brain/index_to_vector.py --search "voice library"
```

## GitHub синхронізація

Нотатки автоматично синхронізуються з GitHub репозиторієм:
- Репозиторій: `vadymvertyan-stack/brain-second-brain`
- Гілка: **notes** (окрема гілка для нотаток)
- Локальний шлях: `/root/brain-second-brain`

## Рекомендації

1. **Викликай після кожної розмови** - не пропускай жодної взаємодії
2. **Витягуй ключові ідеї** - зберігай суть, не повний текст
3. **Додавай теги** - це допоможе в пошуку
4. **Вказуй категорію** - допоможи системі організації
5. **Створюй лінки** - посилання на пов'язані нотатки

## Cron автоматизація

Для періодичного запуску індексації:

```bash
# Додати в crontab
crontab -e

# Індексувати кожні 15 хвилин
*/15 * * * * cd /root/brain-second-brain && python index_to_vector.py >> /var/log/brain-index.log 2>&1

# Резервувати мозок кожну годину
0 * * * * cd /root/brain-second-brain && git add . && git commit -m "Backup: $(date)" && git push origin main >> /var/log/brain-backup.log 2>&1
```

---

*Version: 1.0.0*
*For: Jin (Main Agent)*
*Uses: sync_to_github.py*
