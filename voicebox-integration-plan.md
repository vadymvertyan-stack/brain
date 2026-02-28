# План інтеграції Voicebox у VIBEMODLY

## Резюме

Цей документ описує детальний план інтеграції open-source студії клонування голосу **Voicebox** у систему генерації аудіо-книг **VIBEMODLY**.

---

## 1. Аналіз варіантів інтеграції

### Варіант A: Voicebox як окремий TTS Backend (HTTP API)

**Опис:** Запуск Voicebox як окремого FastAPI сервера, до якого VIBEMODLY звертається через HTTP запити.

**Переваги:**
- Повна ізоляція компонентів
- Можливість масштабування (окремі сервери для TTS)
- Використання всіх функцій Voicebox (профілі, історія, транскрипція)
- Незалежне оновлення компонентів

**Недоліки:**
- ❌ **Несумісність з Google Colab** - Colab не підтримує постійні сервери
- Додаткові накладні витрати на мережеві запити
- Складність деплою для кінцевого користувача
- Неможливість використання GPU Colab для Voicebox сервера

**Оцінка складності:** ⭐⭐⭐⭐ (висока)
**Сумісність з Colab:** ❌ Непридатний

---

### Варіант B: Пряма інтеграція Python модулів

**Опис:** Імпорт модулів Voicebox безпосередньо у код VIBEMODLY.

**Переваги:**
- Мінімальні зміни архітектури
- Використання GPU Colab безпосередньо
- Низькі накладні витрати
- Єдиний процес виконання

**Недоліки:**
- Конфлікти залежностей (різні версії qwen-tts)
- Voicebox використовує **Base моделі** (клонування), VIBEMODLY - **VoiceDesign** (створення голосу)
- Відсутність reference audio у VIBEMODLY (тільки seed + prompt)
- Різні підходи до генерації голосу

**Оцінка складності:** ⭐⭐⭐ (середня)
**Сумісність з Colab:** ⚠️ Частково (з модифікаціями)

---

### Варіант C: Гібридний підхід (рекомендований)

**Опис:** Запозичення архітектурних рішень та окремих компонентів Voicebox з адаптацією під специфіку VIBEMODLY.

**Переваги:**
- ✅ Повна сумісність з Google Colab
- Збереження поточного workflow VIBEMODLY
- Використання перевірених рішень Voicebox
- Поступова міграція без порушення роботи

**Недоліки:**
- Потребує адаптації коду
- Часткове дублювання логіки

**Оцінка складності:** ⭐⭐ (низька)
**Сумісність з Colab:** ✅ Повна

---

### Варіант D: Запозичення архітектурних рішень

**Опис:** Використання патернів та підходів Voicebox без прямого використання коду.

**Переваги:**
- Повна незалежність
- Можливість оптимізації під конкретні потреби
- Відсутність конфліктів залежностей

**Недоліки:**
- Більше роботи з реалізації
- Ризик розбіжностей з оригіналом

**Оцінка складності:** ⭐⭐⭐ (середня)
**Сумісність з Colab:** ✅ Повна

---

## 2. Рекомендований підхід: Гібридний (Варіант C)

### 2.1 Ключові компоненти для інтеграції

| Компонент Voicebox | Застосування у VIBEMODLY |
|-------------------|-------------------------|
| `backends/__init__.py` | Абстракція TTS Engine |
| `utils/cache.py` | Кешування voice prompts |
| `utils/audio.py` | Обробка аудіо |
| `profiles.py` | Управління голосовими профілями |
| `history.py` | Історія генерацій |

### 2.2 Архітектурні зміни

#### 2.2.1 Абстракція TTS Engine

```python
# tts_engine.py - Нова абстракція

from abc import ABC, abstractmethod
from typing import Tuple, Optional
import numpy as np

class TTSEngine(ABC):
    """Абстрактний інтерфейс TTS двигуна"""
    
    @abstractmethod
    async def generate(
        self, 
        text: str, 
        voice_config: dict,
        language: str = "russian"
    ) -> Tuple[np.ndarray, int]:
        """Генерація аудіо з голосовою конфігурацією"""
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """Перевірка завантаження моделі"""
        pass


class VoiceDesignEngine(TTSEngine):
    """VoiceDesign модель (поточний підхід VIBEMODLY)"""
    
    def __init__(self, model_name: str = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"):
        self.model = None
        self.model_name = model_name
    
    async def generate(self, text: str, voice_config: dict, language: str) -> Tuple[np.ndarray, int]:
        seed = voice_config.get("seed")
        prompt = voice_config.get("prompt", "")
        
        # Встановлення seed для детермінізму
        import torch
        import random
        random.seed(seed)
        torch.manual_seed(seed)
        
        # Генерація через VoiceDesign
        result = self.model.generate_voice_design(text, prompt, language)
        return result


class VoiceCloneEngine(TTSEngine):
    """Voice Clone модель (з Voicebox)"""
    
    def __init__(self, model_name: str = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"):
        self.model = None
        self.model_name = model_name
    
    async def generate(self, text: str, voice_config: dict, language: str) -> Tuple[np.ndarray, int]:
        reference_audio = voice_config.get("reference_audio")
        reference_text = voice_config.get("reference_text")
        
        # Створення voice prompt
        voice_prompt = self.model.create_voice_clone_prompt(
            ref_audio=reference_audio,
            ref_text=reference_text
        )
        
        # Генерація через клонування
        result = self.model.generate_voice_clone(
            text=text,
            voice_clone_prompt=voice_prompt
        )
        return result
```

#### 2.2.2 Уніфікація голосових профілів

```python
# voice_profile.py - Уніфікована система профілів

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum

class VoiceMode(Enum):
    VOICE_DESIGN = "voicedesign"  # seed + prompt
    VOICE_CLONE = "clone"         # reference audio


@dataclass
class VoiceProfile:
    """Уніфікований голосовий профіль"""
    id: str
    name: str
    mode: VoiceMode
    
    # VoiceDesign параметри
    seed: Optional[int] = None
    prompt: Optional[str] = None
    
    # Voice Clone параметри
    reference_audio_path: Optional[str] = None
    reference_text: Optional[str] = None
    
    # Загальні параметри
    gender: str = "male"
    language: str = "russian"
    speed: float = 1.0
    pitch: str = "medium"
    
    # Метадані
    description: str = ""
    tags: list = field(default_factory=list)
    
    def to_engine_config(self) -> Dict[str, Any]:
        """Конвертація у конфігурацію для TTS Engine"""
        if self.mode == VoiceMode.VOICE_DESIGN:
            return {
                "mode": "voicedesign",
                "seed": self.seed,
                "prompt": self.prompt,
                "speed": self.speed
            }
        else:
            return {
                "mode": "clone",
                "reference_audio": self.reference_audio_path,
                "reference_text": self.reference_text,
                "speed": self.speed
            }
```

#### 2.2.3 Система кешування (з Voicebox)

```python
# cache.py - Адаптована система кешування

import hashlib
import json
from pathlib import Path
from typing import Optional, Any
import torch

class VoicePromptCache:
    """Кешування voice prompts для пришвидшення генерації"""
    
    def __init__(self, cache_dir: str = "/content/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, Any] = {}
    
    def get_cache_key(self, audio_path: str, text: str) -> str:
        """Генерація ключа кешу"""
        content = f"{audio_path}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Отримання з кешу (memory + disk)"""
        # Спочатку перевіряємо memory cache
        if key in self._memory_cache:
            return self._memory_cache[key]
        
        # Потім disk cache
        cache_file = self.cache_dir / f"{key}.pt"
        if cache_file.exists():
            data = torch.load(cache_file)
            self._memory_cache[key] = data
            return data
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Збереження в кеш"""
        self._memory_cache[key] = value
        cache_file = self.cache_dir / f"{key}.pt"
        torch.save(value, cache_file)
    
    def clear(self) -> None:
        """Очищення кешу"""
        self._memory_cache.clear()
        for f in self.cache_dir.glob("*.pt"):
            f.unlink()
```

### 2.3 Інтеграція з існуючим кодом VIBEMODLY

#### Зміни у `vibemodly_colab.py`

```python
# Додати після ініціалізації моделі

# === ІНТЕГРАЦІЯ VOICEBOX ===
from voicebox_adapter import (
    TTSEngineManager,
    VoiceProfileManager,
    VoicePromptCache
)

# Ініціалізація менеджерів
tts_manager = TTSEngineManager()
profile_manager = VoiceProfileManager()
voice_cache = VoicePromptCache("/content/drive/MyDrive/vibemodly_cache")

# Модифікована функція generate_audio
def generate_audio_v2(
    text: str,
    character_name: str = "narrator",
    voice_preset: Optional[str] = None,
    lang: str = "russian",
    **kwargs
) -> Optional[np.ndarray]:
    """
    Генерація аудіо з підтримкою обох режимів.
    
    Автоматично вибирає режим:
    - VoiceDesign: якщо є seed + prompt
    - VoiceClone: якщо є reference_audio
    """
    # Отримуємо профіль
    profile = profile_manager.get_profile(character_name, voice_preset)
    
    # Отримуємо відповідний engine
    engine = tts_manager.get_engine(profile.mode)
    
    # Перевіряємо кеш
    cache_key = voice_cache.get_cache_key(text, str(profile.to_engine_config()))
    cached = voice_cache.get(cache_key)
    if cached is not None:
        print(f"[CACHE] Використано кеш для {character_name}")
        return cached
    
    # Генеруємо
    config = profile.to_engine_config()
    config["language"] = lang
    
    audio, sr = await engine.generate(text, config, lang)
    
    # Зберігаємо в кеш
    voice_cache.set(cache_key, audio)
    
    return audio
```

---

## 3. План реалізації

### Фаза 1: Підготовка (1-2 дні)

1. **Створення модуля адаптера**
   - `voicebox_adapter/__init__.py`
   - `voicebox_adapter/engine.py`
   - `voicebox_adapter/profile.py`
   - `voicebox_adapter/cache.py`

2. **Додавання залежностей**
   ```
   # Нові залежності для requirements
   librosa>=0.10.0
   soundfile>=0.12.0
   ```

### Фаза 2: Інтеграція (2-3 дні)

1. **Модифікація `vibemodly_colab.py`**
   - Додати імпорт адаптера
   - Замінити пряме використання моделі на TTSEngineManager
   - Додати підтримку reference audio (опціонально)

2. **Розширення системи пресетів**
   - Додати підтримку reference audio у VOICE_PRESETS
   - Створити конвертер старих пресетів у новий формат

### Фаза 3: Тестування (1-2 дні)

1. **Unit тести**
   - Тестування TTSEngine абстракції
   - Тестування кешування
   - Тестування профілів

2. **Integration тести**
   - Повний цикл генерації в Colab
   - Перевірка сумісності з існуючими функціями

### Фаза 4: Документація (1 день)

1. Оновлення README_VIBEMODLY.md
2. Додавання прикладів використання
3. Інструкції з міграції

---

## 4. Нові можливості після інтеграції

| Функція | Опис |
|---------|------|
| **Voice Cloning** | Можливість клонування голосу з reference audio |
| **Кешування prompts** | Пришвидшення повторних генерацій у 3-5 разів |
| **Multi-sample профілі** | Краща якість голосу через комбінування зразків |
| **Універсальні профілі** | Єдиний формат для обох режимів генерації |
| **Fallback механізм** | Автоматичне перемикання між режимами |

---

## 5. Ризики та мітигація

| Ризик | Ймовірність | Вплив | Мітигація |
|-------|-------------|-------|-----------|
| Конфлікт версій qwen-tts | Середня | Високий | Використання умовного імпорту |
| Збільшення використання пам'яті | Висока | Середній | Lazy loading моделей |
| Несумісність з Colab | Низька | Високий | Тестування на кожному етапі |
| Втрата консистентності голосу | Середня | Високий | Збереження seed у профілях |

---

## 6. Висновок

Рекомендований **гібридний підхід (Варіант C)** забезпечує:

1. ✅ Повну сумісність з Google Colab
2. ✅ Збереження поточного workflow користувачів
3. ✅ Розширення можливостей (voice cloning)
4. ✅ Покращення продуктивності (кешування)
5. ✅ Гнучкість для майбутніх розширень

Інтеграція може бути виконана поступово без порушення роботи існуючої системи.

---

## 7. Посилання

- [Voicebox Repository](https://github.com/jamiepine/voicebox)
- [Qwen3-TTS Documentation](https://huggingface.co/Qwen)
- [VIBEMODLY Source](../vibemodly_colab.py)
