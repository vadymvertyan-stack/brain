# План: Screenshot Reader Skill для OpenClaw

## 📋 Огляд

Цей план описує створення навички `screenshot-reader` для агента Jin в OpenClaw, яка використовує Google AI Studio API з моделлю `gemini-3-pro-preview` для аналізу скріншотів.

---

## 🔍 Аналіз існуючої структури

### Формат навичок (Skills)

На основі аналізу файлів у [`brain/skills/`](brain/skills/):

```
brain/skills/
├── brain/
│   └── skill.md          # Second Brain skill
├── brain-jazz/
│   └── skill.md          # Brainstorming skill
└── context-compression/
    └── skill.md          # Context Compression skill
```

**Структура skill.md:**
1. **Заголовок** - назва навички
2. **Опис** - короткий опис призначення
3. **Можливості** - список функціональності
4. **Команди/Інструкції** - як використовувати
5. **Приклади** - практичні приклади
6. **Метадані** - версія, автор, дата

### Структура провайдера OpenClaw

На основі аналізу [`OpenClaw/add_gemini_provider.py`](OpenClaw/add_gemini_provider.py:1):

```python
config['models']['providers']['gemini'] = {
    'baseUrl': 'https://generativelanguage.googleapis.com/v1beta',
    'apiKey': 'API_KEY',
    'models': [
        {
            'id': 'model-id',
            'name': 'Model Name',
            'reasoning': False,
            'input': ['text', 'image'],  # Vision support!
            'cost': {'input': 0, 'output': 0, 'cacheRead': 0, 'cacheWrite': 0},
            'contextWindow': 1000000,
            'maxTokens': 8192
        }
    ]
}
```

**Ключові поля для vision моделей:**
- `input: ['text', 'image']` - підтримка зображень
- `contextWindow` - розмір контекстного вікна
- `maxTokens` - максимальна кількість токенів

---

## 📁 Файли для створення/оновлення

### 1. Нові файли

| Файл | Опис |
|------|------|
| `brain/skills/screenshot-reader/skill.md` | Навичка screenshot-reader |
| `OpenClaw/add_gemini_vision_provider.py` | Скрипт додавання провайдера |

### 2. Файли для оновлення

| Файл | Зміни |
|------|-------|
| `brain/README.md` | Додати інформацію про screenshot-reader skill |

---

## 📝 Детальний план

### Крок 1: Створення skill.md для screenshot-reader

**Шлях:** `brain/skills/screenshot-reader/skill.md`

```markdown
# Screenshot Reader Skill

## Опис
Цей skill надає AI асистенту можливість аналізувати скріншоти та зображення 
з використанням Google Gemini Vision API.

## Можливості
- Аналіз скріншотів програм та веб-сторінок
- Розпізнавання тексту на зображеннях (OCR)
- Опис вмісту зображень
- Відповіді на запитання про зображення
- Витягування даних з візуальних матеріалів

## Модель
- **Провайдер:** Google AI Studio
- **Модель:** gemini-3-pro-preview
- **API Key:** AIzaSyDToumHFOKCS_SM7nC_rWmKR9K_caVyrMI
- **Base URL:** https://generativelanguage.googleapis.com/v1beta

## Команди

### Аналіз скріншота
```
Проаналізуй цей скріншот [зображення]
```

### Розпізнавання тексту
```
Розпізнай текст на цьому зображенні [зображення]
```

### Опис зображення
```
Опиши що ти бачиш на цьому зображенні [зображення]
```

### Витягування даних
```
Витягни [дані] з цього скріншота [зображення]
```

## Використання в OpenClaw

### Налаштування провайдера
Провайдер Google AI Studio повинен бути доданий до конфігурації OpenClaw:

```json
{
  "models": {
    "providers": {
      "google-ai-studio": {
        "baseUrl": "https://generativelanguage.googleapis.com/v1beta",
        "apiKey": "AIzaSyDToumHFOKCS_SM7nC_rWmKR9K_caVyrMI",
        "models": [...]
      }
    }
  }
}
```

### Fallbacks
Модель gemini-3-pro-preview може бути додана до fallbacks:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "fallbacks": ["google-ai-studio/gemini-3-pro-preview"]
      }
    }
  }
}
```

## Приклади використання

### Приклад 1: Аналіз скріншота помилки
```
Користувач: [надсилає скріншот помилки]
AI: Бачу помилку на скріншоті. Це помилка підключення до бази даних...
```

### Приклад 2: Розпізнавання коду
```
Користувач: [надсилає скріншот з кодом]
AI: Ось код з зображення:
function example() {
  return "Hello World";
}
```

### Приклад 3: Аналіз UI
```
Користувач: Опиши інтерфейс на цьому скріншоті
AI: На скріншоті зображено головне вікно програми...
```

## Обмеження
- Максимальний розмір зображення: 20MB
- Підтримувані формати: PNG, JPEG, WebP, GIF
- Контекстне вікно: залежить від моделі

---
*Version: 1.0.0*
*Author: Kilo Code*
*Created: 2026-02-21*
```

---

### Крок 2: Створення скрипта додавання провайдера

**Шлях:** `OpenClaw/add_gemini_vision_provider.py`

```python
#!/usr/bin/env python3
"""
Додавання провайдера Google AI Studio з моделлю gemini-3-pro-preview 
для навички screenshot-reader.

Цей скрипт додає vision-модель для аналізу зображень та скріншотів.
"""

import json
import subprocess
import tempfile
import os

# Google AI Studio provider configuration
GOOGLE_AI_STUDIO_PROVIDER = {
    "baseUrl": "https://generativelanguage.googleapis.com/v1beta",
    "apiKey": "AIzaSyDToumHFOKCS_SM7nC_rWmKR9K_caVyrMI",
    "models": [
        {
            "id": "gemini-3-pro-preview",
            "name": "Gemini 3 Pro Preview",
            "reasoning": False,
            "input": ["text", "image"],  # Vision support!
            "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
            "contextWindow": 1000000,
            "maxTokens": 8192,
            "description": "Vision модель для аналізу скріншотів"
        }
    ]
}

def get_current_config():
    """Отримує поточну конфігурацію з сервера."""
    cmd = "cat /root/.openclaw/openclaw.json"
    result = subprocess.run(
        ["ssh", "root@164.68.111.47", cmd],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Помилка отримання конфігурації: {result.stderr}")
        return None
    
    return json.loads(result.stdout)

def update_config():
    """Оновлює конфігурацію OpenClaw, додаючи Google AI Studio провайдер."""
    
    print("🔍 Додавання Google AI Studio провайдера до OpenClaw...")
    print("=" * 50)
    
    # Отримуємо поточну конфігурацію
    config = get_current_config()
    if not config:
        return False
    
    # Ініціалізуємо структуру якщо потрібно
    if "models" not in config:
        config["models"] = {}
    if "providers" not in config["models"]:
        config["models"]["providers"] = {}
    
    # Додаємо провайдер Google AI Studio
    config["models"]["providers"]["google-ai-studio"] = GOOGLE_AI_STUDIO_PROVIDER
    print(f"  ➕ Додано провайдер: google-ai-studio")
    print(f"  ➕ Додано модель: gemini-3-pro-preview (vision)")
    
    # Додаємо до fallbacks
    if "agents" not in config:
        config["agents"] = {}
    if "defaults" not in config["agents"]:
        config["agents"]["defaults"] = {}
    if "model" not in config["agents"]["defaults"]:
        config["agents"]["defaults"]["model"] = {}
    if "fallbacks" not in config["agents"]["defaults"]["model"]:
        config["agents"]["defaults"]["model"]["fallbacks"] = []
    
    model_id = "google-ai-studio/gemini-3-pro-preview"
    if model_id not in config["agents"]["defaults"]["model"]["fallbacks"]:
        config["agents"]["defaults"]["model"]["fallbacks"].append(model_id)
        print(f"  ➕ Додано до fallbacks: {model_id}")
    
    # Додаємо model alias
    if "models" not in config["agents"]["defaults"]:
        config["agents"]["defaults"]["models"] = {}
    
    config["agents"]["defaults"]["models"][model_id] = {
        "alias": "Gemini 3 Pro Preview (Vision)"
    }
    
    # Додаємо auth profile
    if "auth" not in config:
        config["auth"] = {}
    if "profiles" not in config["auth"]:
        config["auth"]["profiles"] = {}
    
    config["auth"]["profiles"]["google-ai-studio:default"] = {
        "provider": "google-ai-studio",
        "mode": "api_key"
    }
    print(f"  ➕ Додано auth profile: google-ai-studio:default")
    
    # Зберігаємо оновлену конфігурацію
    config_json = json.dumps(config, indent=2, ensure_ascii=False)
    
    # Створюємо тимчасовий файл
    temp_file = os.path.join(tempfile.gettempdir(), "openclaw_gemini_vision.json")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(config_json)
    
    # Копіюємо файл на сервер
    scp_result = subprocess.run(
        ["scp", temp_file, "root@164.68.111.47:/tmp/openclaw_gemini_vision.json"],
        capture_output=True,
        text=True
    )
    
    if scp_result.returncode != 0:
        print(f"❌ Помилка копіювання: {scp_result.stderr}")
        return False
    
    # Оновлюємо конфігурацію на сервері
    update_cmd = (
        "cp /root/.openclaw/openclaw.json /root/.openclaw/openclaw.json.bak.gemini-vision && "
        "mv /tmp/openclaw_gemini_vision.json /root/.openclaw/openclaw.json"
    )
    update_result = subprocess.run(
        ["ssh", "root@164.68.111.47", update_cmd],
        capture_output=True,
        text=True
    )
    
    if update_result.returncode != 0:
        print(f"❌ Помилка оновлення: {update_result.stderr}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Конфігурацію успішно оновлено!")
    print("✅ Google AI Studio провайдер додано")
    print("✅ Модель gemini-3-pro-preview готова до використання")
    
    return True

if __name__ == "__main__":
    update_config()
```

---

### Крок 3: Оновлення README.md

Додати до [`brain/README.md`](brain/README.md:1) в розділ `skills/`:

```markdown
- **screenshot-reader/** - Screenshot Reader skill для аналізу зображень
```

---

## 🔄 Діаграма процесу

```mermaid
flowchart TD
    A[Початок] --> B[Створити skill.md]
    B --> C[Створити скрипт провайдера]
    C --> D[Запустити скрипт на VPS]
    D --> E{Конфігурація оновлена?}
    E -->|Так| F[Оновити README.md]
    E -->|Ні| G[Виправити помилки]
    G --> D
    F --> H[Тестування навички]
    H --> I[Кінець]
```

---

## 📊 Структура конфігурації OpenClaw

```mermaid
graph TD
    subgraph OpenClaw Config
        A[models.providers] --> B[google-ai-studio]
        B --> C[baseUrl]
        B --> D[apiKey]
        B --> E[models]
        E --> F[gemini-3-pro-preview]
        F --> G[input: text, image]
        F --> H[contextWindow: 1M]
        
        I[agents.defaults] --> J[model.fallbacks]
        J --> K[google-ai-studio/gemini-3-pro-preview]
        
        L[auth.profiles] --> M[google-ai-studio:default]
    end
```

---

## ✅ Чекліст виконання

- [ ] Створити директорію `brain/skills/screenshot-reader/`
- [ ] Створити файл `brain/skills/screenshot-reader/skill.md`
- [ ] Створити файл `OpenClaw/add_gemini_vision_provider.py`
- [ ] Запустити скрипт на VPS для оновлення конфігурації
- [ ] Оновити `brain/README.md`
- [ ] Протестувати навичку з реальним скріншотом

---

## 🛡️ Безпека

⚠️ **Увага:** API ключ `AIzaSyDToumHFOKCS_SM7nC_rWmKR9K_caVyrMI` зберігається в коді. 

**Рекомендації:**
1. Використовувати змінні середовища для API ключів
2. Зберігати ключі в `credentials/` директорії OpenClaw
3. Не комітити API ключі в публічні репозиторії

---

## 📚 Додаткові ресурси

- [Google AI Studio API Docs](https://ai.google.dev/docs)
- [Gemini API Reference](https://ai.google.dev/api)
- [OpenClaw Documentation](./OpenClaw/)
