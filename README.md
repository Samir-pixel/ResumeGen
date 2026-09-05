# AI Resume Generator

Генератор профессиональных резюме на основе описания вакансии.

Пользователь вставляет текст вакансии — система автоматически:
1. Анализирует требования
2. Создаёт реалистичную карьерную историю кандидата
3. Генерирует компании, проекты, команды и рабочий опыт
4. Проверяет консистентность
5. Пишет профессиональный текст резюме
6. Рендерит HTML → PDF
7. Возвращает готовый PDF для скачивания

---

## Технологии

| Слой | Стек |
|------|------|
| Backend | Python 3.12, FastAPI, Pydantic 2, Celery, SQLAlchemy |
| LLM | OpenAI API (опционально) или эвристика |
| PDF | HTML/CSS + Playwright/Chromium (или ReportLab fallback) |
| Frontend | Next.js 16, React 18, TypeScript, Tailwind CSS |
| Инфраструктура | Docker, Docker Compose, Redis, PostgreSQL |

---

## Быстрый старт

### 1. Клонировать и настроить окружение

```bash
git clone <repo>
cd resume-generator
cp .env.example .env
```

### 2. (Опционально) Добавить OpenAI API ключ в `.env`

```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

Без ключа система работает в режиме эвристики (быстро, без LLM).

### 3. Запустить через Docker Compose

```bash
docker compose up --build
```

Сервисы:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### 4. Проверить работоспособность

```bash
curl http://localhost:8000/health
```

---

## Локальная разработка без Docker

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Тесты

```bash
cd backend
pytest tests/ -v
```

---

## API

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/health` | Health check |
| POST | `/api/v1/generations` | Создать задание генерации |
| GET | `/api/v1/generations/{id}` | Статус генерации |
| GET | `/api/v1/resumes/{id}/preview` | HTML превью |
| GET | `/api/v1/resumes/{id}/pdf` | Скачать PDF |

### Создать генерацию

```http
POST /api/v1/generations
Content-Type: application/json

{
  "vacancy_text": "Middle Python Backend Developer..."
}
```

Ответ:
```json
{
  "generation_id": "uuid",
  "status": "queued"
}
```

### Статусы генерации

```
queued → analyzing_vacancy → generating_candidate →
generating_companies → generating_projects → generating_experience →
validating → writing_resume → criticizing →
rendering_pdf → validating_pdf → completed
```

---

## Структура проекта

```
resume-generator/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI роуты
│   │   ├── core/          # Конфигурация, логирование
│   │   ├── models/        # SQLAlchemy модели
│   │   ├── repositories/  # Слой хранения данных
│   │   ├── schemas/       # Pydantic схемы
│   │   ├── services/      # Бизнес-логика и генераторы
│   │   │   ├── llm/       # LLM провайдеры
│   │   │   ├── vacancy_analyzer.py
│   │   │   ├── career_generator.py
│   │   │   ├── company_generator.py
│   │   │   ├── project_generator.py
│   │   │   ├── experience_generator.py
│   │   │   ├── consistency_validator.py
│   │   │   ├── resume_writer.py
│   │   │   ├── resume_critic.py
│   │   │   ├── pdf_renderer.py
│   │   │   └── pdf_validator.py
│   │   └── workers/       # Celery задачи
│   └── tests/
├── frontend/              # Next.js приложение
├── prompts/               # Промпты для LLM сервисов
├── templates/
│   └── modern/            # HTML/CSS шаблон резюме
├── storage/               # Сгенерированные файлы
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Режимы работы

### Эвристический (по умолчанию)

Быстрая генерация без API ключей. Использует шаблоны и встроенную базу знаний.

```env
LLM_PROVIDER=heuristic
```

### OpenAI

Высококачественная генерация через LLM. Требует `LLM_API_KEY`.

```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

---

## Definition of Done

- [x] Пользователь вставляет вакансию
- [x] Вакансия анализируется (12 полей)
- [x] Генерируется карьерная история (кандидат, компании, проекты, команды)
- [x] Генерируется рабочий опыт с причинно-следственной структурой
- [x] Консистентность карьеры проверяется и при необходимости регенерируется
- [x] Создаётся Resume JSON (Pydantic-валидированный)
- [x] Создаётся HTML по шаблону Jinja2
- [x] Генерируется PDF (Playwright + ReportLab fallback)
- [x] PDF валидируется
- [x] PDF доступен через GET /api/v1/resumes/{id}/pdf
- [x] Frontend показывает прогресс этапов
- [x] Кнопка Download PDF работает
- [x] Polling каждые 2 секунды
- [x] Error handling на каждом этапе
- [x] 13 тестов проходят
- [x] Docker Compose
- [x] README
- [x] Секреты только через env variables
