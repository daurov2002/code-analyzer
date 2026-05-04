# KodTahlil — Dastur Matnini Toza Kod Uslublari Asosida Tekshiruvchi Tizim

BMI loyihasi: "Dastur matnini toza kod yozish uslublari asosida tekshiruvchi dasturiy majmuani yaratish"

## Tizim tuzilmasi

```
code-analyzer/
├── backend/
│   ├── main.py           # FastAPI backend
│   ├── requirements.txt  # Python kutubxonalar
│   ├── .env.example      # Konfiguratsiya namunasi
│   └── README.md
├── frontend/
│   └── index.html        # To'liq frontend (single-file)
└── README.md
```

## O'rnatish va ishga tushirish

### 1. Backend

```bash
cd backend

# Virtual muhit yaratish (tavsiya)
python -m venv venv
source venv/bin/activate       # Linux/Mac
# yoki
venv\Scripts\activate          # Windows

# Kutubxonalarni o'rnatish
pip install -r requirements.txt

# API kalitini sozlash
cp .env.example .env
# .env faylini oching va OPENAI_API_KEY ni kiriting

# Serverni ishga tushirish
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend manzili: http://localhost:8000
API hujjatlari: http://localhost:8000/docs

### 2. Frontend

```bash
# frontend/index.html faylini brauzerda oching
# yoki oddiy server orqali:
cd frontend
python -m http.server 3000
# Keyin: http://localhost:3000
```

## Foydalanish

1. Frontendni brauzerda oching
2. Backend URL ni tekshiring (standart: http://localhost:8000)
3. Kod kiriting (namuna kod avtomatik ko'rsatiladi)
4. Dasturlash tilini tanlang
5. Vazifa turini tanlang: Review / Fix / Explain / Refactor
6. "Tahlil Qilish" tugmasini bosing (yoki Ctrl+Enter)

## Texnologiyalar

| Qism     | Texnologiya        |
|----------|--------------------|
| Backend  | Python + FastAPI   |
| Validatsiya | Pydantic        |
| AI tahlil | OpenAI GPT-4o-mini |
| Lint     | Flake8 (Python)    |
| Frontend | HTML5 + CSS3 + JS  |
| Muharrir | CodeMirror 5       |

## API Endpointlar

### POST /api/analyze

So'rov:
```json
{
  "language": "python",
  "task": "review",
  "instruction": "nomlash va SRP tamoyiliga e'tibor bering",
  "code": "def f(a,b):\n    return a+b"
}
```

Javob:
```json
{
  "fixed_code": "def calculate_sum(first: int, second: int) -> int:\n    return first + second",
  "explanation": "Funksiya to'g'ri ishlaydi, lekin...",
  "issues": ["Funksiya nomi 'f' tavsiflovchi emas", "Tip annotatsiyalari yo'q"],
  "suggestions": ["Parametrlarga mazmunli nom bering", "-> return type qo'shing"],
  "score": 45,
  "lint_output": "1:7: E741 ambiguous variable name 'f'"
}
```

## Litsenziya

Bitiruv malakaviy ish doirasida yaratilgan. Barcha huquqlar himoyalangan.
