# Large Plans Skill

## Опис
Цей skill автоматично управляє виконанням великих планів, запобігаючи зацикленню, обробляючи API помилки та забезпечуючи відновлення після збоїв.

## Аналіз проблеми

### Типи планів за складністю

| Категорія | Розмір | Рядків | Етапів | Приклад |
|-----------|--------|--------|--------|---------|
| Малий | < 10KB | < 300 | 1-3 | bug fix, minor feature |
| Середній | 10-30KB | 300-1000 | 3-5 | feature implementation |
| Великий | 30-60KB | 1000-2000 | 5-10 | architecture redesign |
| Гігантський | > 60KB | > 2000 | > 10 | full system migration |

### Виявлені проблеми при виконанні великих планів

1. **API помилки**
   - Помилка `api` налаштування (не встановлено `openai-completions`)
   - Помилка ID моделі (невірний формат)
   - Помилка конфігурації провайдерів (MiniMax, NVIDIA)
   - Помилка Slack dmPolicy
   - Помилка ліміту ключа (403 Key limit exceeded)

2. **Найпроблемніші провайдери**
   - MiniMax (конфігурація, model ID)
   - NVIDIA (прямі помилки API)
   - Slack (dmPolicy помилки)

3. **Зациклення**
   - Повторні ідентичні запити > 3 разів
   - Ознака втрати прогресу
   - Повторне читання тих самих файлів

## Автоматичні тригери

### Порогові значення
```
ТРИГЕР АКТИВАЦІЇ:
- План > 2000 рядків АБО > 50KB
- Кількість етапів > 5
- Ознаки API помилок в контексті
- Повторні ідентичні запити (однаковий запит > 3 разів)
- Контекст > 70% від ліміту
```

### Виявлення API помилок
```
ПАТЕРНИ ПОМИЛОК:
- "api error" | "API error" | "api_error"
- "provider.*error" | "configuration.*failed"
- "403" | "429" | "500" | "502" | "503"
- "Key limit exceeded" | "Rate limit"
- "MiniMax" | "NVIDIA" | "Slack" (у контексті помилки)
- "dmPolicy" | "model.*not found"
```

## Механізми обробки

### 1. Чанкування плану

```
АЛГОРИТМ CHUNK_PLAN:
Вхід: plan_content, target_chunk_size=500 рядків

1. Розбити план на секції за заголовками (#, ##, ###)
2. Для кожної секції:
   a. Визначити залежності (файли, API, зовнішні сервіси)
   b. Оцінити складність (низька/середня/висока)
   c. Визначити точки ризику (API виклики, зовнішні залежності)
3. Згрупувати секції в chunks:
   - Кожен chunk = незалежна одиниця виконання
   - Максимальний розмір chunk = target_chunk_size
   - Мінімальний набір залежностей між chunks
4. Повернути список chunks з метаданими

Вихід: [
  {
    "id": "chunk_1",
    "sections": ["Вступ", "Аналіз"],
    "dependencies": [],
    "risk_points": [],
    "complexity": "low",
    "estimated_tokens": 2000
  },
  ...
]
```

### 2. Система чекпоінтів

```json
{
  "checkpoint_schema": {
    "plan_id": "string (hash плану)",
    "created_at": "ISO 8601 timestamp",
    "updated_at": "ISO 8601 timestamp",
    "status": "in_progress | completed | failed | paused",
    "current_chunk": "number",
    "total_chunks": "number",
    "completed_chunks": ["chunk_1", "chunk_2"],
    "failed_chunks": [
      {
        "chunk_id": "chunk_3",
        "error_type": "api_error",
        "error_message": "MiniMax provider failed",
        "retry_count": 2,
        "last_attempt": "2026-02-21T10:00:00Z"
      }
    ],
    "context_summary": {
      "files_modified": ["file1.py", "file2.ts"],
      "files_created": ["new_file.py"],
      "key_decisions": ["Використано підхід X замість Y"],
      "pending_questions": []
    },
    "api_state": {
      "current_provider": "openai",
      "failed_providers": ["minimax", "nvidia"],
      "rate_limits": {
        "openai": {"remaining": 50, "reset_at": "..."},
        "anthropic": {"remaining": 100, "reset_at": "..."}
      }
    },
    "recovery_info": {
      "last_successful_step": "Створено файл voice_library_manager.py",
      "next_step": "Модифікувати generate_audio()",
      "rollback_available": true
    }
  }
}
```

### 3. Експоненційний backoff при API помилках

```
АЛГОРИТМ EXPONENTIAL_BACKOFF:
Вхід: error, current_retry, max_retries=5

1. Якщо current_retry >= max_retries:
   - Спробувати альтернативного провайдера
   - Якщо немає альтернативи → pause план, повідомити користувача

2. Розрахувати затримку:
   base_delay = 1 секунда
   max_delay = 60 секунд
   delay = min(base_delay * 2^current_retry, max_delay)
   jitter = random(0, delay * 0.1)  # Додаємо випадковість
   final_delay = delay + jitter

3. Зачекати final_delay секунд

4. Повторити запит

ПОВЕРНУТИ: {success: bool, retry_count: number, next_delay: number}
```

### 4. Детекція зациклення

```
АЛГОРИТМ DETECT_LOOP:
Вхід: request_history (останні 20 запитів)

1. Для кожного запиту в історії:
   - Створити хеш від: query + parameters + context_summary
   - Зберегти в sliding window

2. Підрахувати кількість однакових хешів:
   - Якщо count >= 3 → ВИЯВЛЕНО ЗАЦИКЛЕННЯ

3. При виявленні зациклення:
   a. Зупинити виконання
   b. Проаналізувати причину:
      - Втрата контексту? → Стиснути контекст, відновити з checkpoint
      - API помилка? → Змінити провайдера
      - Логічна помилка? → Запитати користувача
   c. Запропонувати рішення

ВИХІД: {
  loop_detected: bool,
  loop_type: "context_loss" | "api_failure" | "logic_error",
  recommendation: string
}
```

### 5. Автоматичне перемикання провайдера

```
АЛГОРИТМ SWITCH_PROVIDER:
Вхід: failed_provider, error_type

1. Визначити пріоритет провайдерів за типом задачі:
   code_tasks: ["openai", "anthropic", "gemini", "deepseek"]
   analysis_tasks: ["anthropic", "openai", "gemini"]
   creative_tasks: ["openai", "anthropic"]

2. Вибрати наступного провайдера:
   - Не в failed_providers
   - З найбільшим remaining rate limit
   - Згідно з пріоритетом

3. Перевірити доступність:
   - Зробити тестовий запит
   - Якщо успішно → переключитись
   - Якщо ні → спробувати наступного

4. Зберегти стан перемикання в checkpoint

ВИХІД: {
  new_provider: string,
  available: bool,
  fallback_used: bool
}
```

## Інтеграція з іншими skills

### З context-compression

```
ІНТЕГРАЦІЯ:
1. При досягненні 70% контексту:
   - large-plans зберігає checkpoint
   - context-compression стискає неактивні частини
   - large-plans відновлює роботу з checkpoint

2. При втраті контексту:
   - large-plans виявляє зациклення
   - context-compression надає summary
   - large-plans відновлює прогрес
```

### З brain

```
ІНТЕГРАЦІЯ:
1. Збереження прогресу:
   - Кожен checkpoint → brain/memory/YYYY-MM-DD.md
   - Формат: ## Plan Progress: [plan_name]

2. Відновлення:
   - При старті перевірити brain/memory/ на наявність незавершених планів
   - Запропонувати продовження
```

## Алгоритми виконання

### Головний алгоритм виконання плану

```
АЛГОРИТМ EXECUTE_LARGE_PLAN:
Вхід: plan_content, options

1. ІНІЦІАЛІЗАЦІЯ:
   - Розрахувати хеш плану → plan_id
   - Перевірити наявність checkpoint для plan_id
   - Якщо checkpoint існує → запитати про продовження
   - Якщо ні → створити новий checkpoint

2. АНАЛІЗ ПЛАНУ:
   - Виконати CHUNK_PLAN
   - Оцінити ризики для кожного chunk
   - Визначити критичні залежності

3. ВИКОНАННЯ (для кожного chunk):
   a. Перевірити тригери:
      - Контекст > 70%? → викликати context-compression
      - API помилка? → EXPONENTIAL_BACKOFF
      - Зациклення? → DETECT_LOOP + відновлення
   
   b. Виконати chunk:
      - Читати тільки необхідні файли
      - Застосовувати зміни
      - Валідувати результат
   
   c. Оновити checkpoint:
      - Зберегти прогрес
      - Оновити api_state
      - Записати key_decisions

4. ЗАВЕРШЕННЯ:
   - Позначити checkpoint як completed
   - Зберегти summary в brain
   - Повідомити користувача

ВИХІД: {success: bool, completed_chunks: number, summary: string}
```

### Алгоритм відновлення після збою

```
АЛГОРИТМ RECOVER_FROM_FAILURE:
Вхід: checkpoint, error

1. Визначити тип помилки:
   - API_ERROR → спробувати іншого провайдера
   - CONTEXT_OVERFLOW → стиснути контекст
   - VALIDATION_ERROR → відкотити зміни
   - UNKNOWN → запитати користувача

2. Відновити стан:
   - Завантажити останній успішний checkpoint
   - Відкотити невдалі зміни (якщо є rollback)
   - Оновити контекст з summary

3. Продовжити виконання:
   - Почати з next_step
   - Застосувати нову стратегію (інший провайдер/підхід)

ВИХІД: {recovered: bool, next_action: string}
```

## Практичні рекомендації

### Для AI при роботі з великими планами

```
ПЕРЕД ПОЧАТКОМ:
1. Оцінити розмір плану
2. Якщо > 50KB або > 5 етапів:
   - Активувати large-plans skill
   - Створити checkpoint
   - Розбити на chunks

ПІД ЧАС ВИКОНАННЯ:
1. Після кожного етапу:
   - Зберегти прогрес в checkpoint
   - Оновити brain/memory
2. При API помилці:
   - Не повторювати одразу
   - Застосувати backoff
   - Спробувати іншого провайдера
3. При ознаках зациклення:
   - Зупинитись
   - Проаналізувати причину
   - Відновити з checkpoint

ПІСЛЯ ЗАВЕРШЕННЯ:
1. Зберегти summary в brain
2. Очистити тимчасові дані
3. Повідомити про результат
```

### Для користувачів

```
ЯКЩО ПЛАН ВЕЛИКИЙ:
- Дозвольте AI працювати поетапно
- Не переривайте без необхідності
- Перевіряйте прогрес у brain/memory

ЯКЩО СТАЛАСЯ ПОМИЛКА:
- AI автоматично спробує інший підхід
- Прогрес збережено в checkpoint
- Можна продовжити пізніше
```

## Метрики та моніторинг

```
МЕТРИКИ ЕФЕКТИВНОСТІ:
- Час виконання на chunk
- Кількість retry на API помилки
- Відсоток успішних chunk без retry
- Час відновлення після збою
- Відсоток збереженого контексту

ПОРОГОВІ ЗНАЧЕННЯ:
- Макс. retry на chunk: 5
- Макс. час на chunk: 10 хвилин
- Мін. збережений контекст: 80%
```

## Приклади використання

### Приклад 1: Виконання великого архітектурного плану

```
AI: "Бачу план voice-library-manager-architecture.md (55KB, 1821 рядків).
     Активую large-plans skill.
     
     Аналіз:
     - 9 основних секцій
     - 4 фази реалізації
     - Потенційні точки ризику: Google Drive API, TTS model loading
     
     Стратегія:
     1. Chunk 1: Аналіз + Архітектура (без ризиків)
     2. Chunk 2: Схема даних + Drive інтерфейс
     3. Chunk 3: Валідація + Інтеграція
     4. Chunk 4: Тестування
     
     Створено checkpoint: chk_vlib_20260221
     
     Починаю виконання з Chunk 1..."
```

### Приклад 2: Обробка API помилки

```
AI: "Отримано помилку від MiniMax provider: 'model not found'
     
     Дії:
     1. Збережено checkpoint (chunk 2, крок 3)
     2. MiniMax додано до failed_providers
     3. Перемикання на openai-completions
     4. Продовження з останнього успішного кроку...
     
     Прогрес збережено. Продовжую виконання."
```

### Приклад 3: Виявлення зациклення

```
AI: "⚠️ Виявлено зациклення: однаковий запит повторено 4 рази.
     
     Аналіз:
     - Причина: Втрата контексту після стискання
     - Останній успішний крок: Створено voice_library_manager.py
     
     Відновлення:
     1. Завантажено checkpoint від 10:30
     2. Відновлено контекст з summary
     3. Продовження з кроку: 'Модифікація generate_audio()'
     
     Продовжую виконання..."
```

---

*Version: 1.0.0*
*Author: Kilo Code*
*Created: 2026-02-21*
