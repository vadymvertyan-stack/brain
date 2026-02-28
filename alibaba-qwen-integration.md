# План інтеграції Alibaba Cloud Qwen в OpenClaw

## Статус виконання

- [x] Проаналізувати безкоштовні ліміти Alibaba Cloud (3 млн токенів до 13.03.2026)
- [x] Дослідити моделі Qwen (qwen-turbo, qwen-plus, qwen-long)
- [x] Створити план інтеграції Alibaba Cloud в OpenClaw
- [ ] Створити DashScope API Key в Alibaba Cloud Console
- [ ] Підключитись до VPS і перевірити структуру OpenClaw
- [ ] Налаштувати credentials файл для Alibaba Cloud
- [ ] Протестувати підключення Qwen
- [ ] Додати wiro.ai API (4 ключі по $100)

---

## Ваші безкоштовні ліміти (до 13.03.2026)

| Модель | Токени | Опис |
|--------|--------|------|
| **qwen-long** | 1,000,000 | Для довгих контекстів |
| **qwen-turbo** | 1,000,000 | Швидка модель |
| **qwen-plus** | 1,000,000 | Збалансована модель |
| **ВСЬОГО** | **3,000,000** | |

## Моделі Qwen та їх призначення

### qwen-turbo
- Найшвидша модель
- Оптимальна для простих завдань
- Низька затримка відповіді

### qwen-plus
- Збалансована модель
- Краща якість відповідей
- Підходить для більшості завдань

### qwen-long
- Підтримка довгого контексту
- Оптимальна для аналізу великих документів
- Більше вхідних токенів

## Варіанти інтеграції в OpenClaw

### Варіант 1: Через OpenAI-сумісний API (рекомендовано)

Alibaba Cloud DashScope підтримує OpenAI-сумісний інтерфейс:

```json
{
  "provider": "openai",
  "apiKey": "sk-xxxxxxxx",
  "baseURL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "model": "qwen-plus"
}
```

**Моделі для використання:**
- `qwen-turbo`
- `qwen-plus`
- `qwen-long`

### Варіант 2: Нативний DashScope API

Якщо OpenClaw підтримує Alibaba Cloud напряму:

```json
{
  "provider": "alibaba",
  "accessKeyId": "YOUR_ACCESS_KEY_ID",
  "accessKeySecret": "YOUR_ACCESS_KEY_SECRET",
  "model": "qwen-plus"
}
```

## Кроки для інтеграції

### Крок 1: Підключитись до VPS
```bash
ssh -i C:\Users\Vadym\.ssh\id_ed25519 root@164.68.111.47
```

### Крок 2: Перевірити структуру credentials
```bash
ls -la /root/.openclaw/credentials/
cat /root/.openclaw/config.json
```

### Крок 3: Створити файл credentials для Alibaba Cloud

**Варіант A - OpenAI-сумісний формат:**
```bash
cat > /root/.openclaw/credentials/alibaba.json << 'EOF'
{
  "provider": "openai",
  "apiKey": "sk-YOUR_DASHSCOPE_API_KEY",
  "baseURL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "models": ["qwen-turbo", "qwen-plus", "qwen-long"]
}
EOF
```

**Варіант B - Якщо потрібен API Key з AccessKey:**
1. Зайти в Alibaba Cloud Console
2. Перейти в DashScope → API-KEY Management
3. Створити новий API Key (це не те саме що AccessKey!)

### Крок 4: Оновити конфігурацію OpenClaw
```bash
# Переглянути поточну конфігурацію
cat /root/.openclaw/config.json

# Додати провайдера в конфігурацію
```

### Крок 5: Перезапустити OpenClaw
```bash
systemctl --user restart openclaw-gateway
```

## Важливо: AccessKey vs API Key

| Тип | Використання |
|-----|--------------|
| **AccessKey ID + Secret** | Для SDK, Terraform, CLI |
| **DashScope API Key** | Для REST API (OpenAI-сумісний інтерфейс) |

Для OpenClaw потрібен **DashScope API Key**, який створюється:
1. Alibaba Cloud Console → DashScope
2. API-KEY Management → Create API Key
3. Формат: `sk-xxxxxxxx`

## Інструкція: Створення DashScope API Key

### Крок 1: Зайти в Alibaba Cloud Console
1. Відкрийте: https://dashscope.console.aliyun.com/
2. Або через головне меню: Console → DashScope

### Крок 2: Створити API Key
1. У лівому меню виберіть **"API-KEY Management"**
2. Натисніть **"Create API Key"**
3. Скопіюйте ключ (формат: `sk-xxxxxxxxxxxxxxxx`)

### Крок 3: Зберегти ключ
⚠️ **Важливо:** Ключ показується тільки один раз!

---

## Наступні кроки

1. ✅ Підключитись до VPS для аналізу структури OpenClaw
2. ✅ Перевірити які провайдери підтримуються
3. ⏳ Створити DashScope API Key (потрібно зробити вам)
4. ⏳ Налаштувати credentials файл
5. ⏳ Протестувати підключення

---

## Після створення API Key

Коли у вас буде DashScope API Key, потрібно буде:

1. Підключитись до VPS:
   ```bash
   ssh -i C:\Users\Vadym\.ssh\id_ed25519 root@164.68.111.47
   ```

2. Перевірити структуру OpenClaw:
   ```bash
   cat /root/.openclaw/config.json
   ls -la /root/.openclaw/credentials/
   ```

3. Створити файл credentials для Alibaba Cloud
