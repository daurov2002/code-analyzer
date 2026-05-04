"""
Dastur matnini toza kod yozish uslublari asosida tekshiruvchi dasturiy majmua
Backend: FastAPI asosida yaratilgan
"""

import os, re, json, subprocess, tempfile
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import httpx












OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_CODE_LENGTH = 15000
SUPPORTED_LANGUAGES = ["python", "javascript", "typescript", "java", "cpp", "go", "rust"]

TASK_PROMPTS = {
    "review": "Kodni toza kod tamoyillari (Clean Code) asosida batafsil ko'rib chiqqin. Nomlash, SRP, DRY, SOLID, o'qiluvchanlik va modullilikka e'tibor ber.",
    "fix": "Kodni tekshirib barcha xatolar, potentsial muammolar va mantiq xatolarini topib tuzat.",
    "explain": "Kodni boshlang'ich dasturchi uchun ham tushunarli tarzda batafsil tushuntir. Algoritmni, har bir funksiyaning maqsadini izohla.",
    "refactor": "Kodni toza kod tamoyillari asosida qayta tuz. Funksiyalarni ajrat, nomlarni yaxshila, takrorlanishlarni yo'qot.",
}

SYSTEM_PROMPT = """Sen yuqori malakali dasturiy injinirlik eksperti va toza kod mutaxassisisan.
Javobni FAQAT quyidagi JSON formatida qaytargin:
{
    "fixed_code": "tuzatilgan kod (bo'lmasa bo'sh string)",
    "explanation": "batafsil tushuntirish",
    "issues": ["muammo 1", "muammo 2"],
    "suggestions": ["tavsiya 1", "tavsiya 2"],
    "score": 0-100 orasidagi son
}"""

class AnalyzeRequest(BaseModel):
    language: str
    task: str
    instruction: Optional[str] = ""
    code: str

    @validator("code")
    def code_not_empty(cls, v):
        if not v or not v.strip(): raise ValueError("Kod bo'sh bo'lmasligi kerak")
        if len(v) > MAX_CODE_LENGTH: raise ValueError(f"Kod {MAX_CODE_LENGTH} belgidan oshmasligi kerak")
        return v

    @validator("task")
    def task_valid(cls, v):
        if v not in TASK_PROMPTS: raise ValueError(f"Noto'g'ri vazifa: {list(TASK_PROMPTS.keys())}")
        return v

    @validator("language")
    def lang_valid(cls, v):
        if v.lower() not in SUPPORTED_LANGUAGES: raise ValueError(f"Til qo'llab-quvvatlanmaydi")
        return v.lower()

class AnalyzeResponse(BaseModel):
    fixed_code: str = ""
    explanation: str = ""
    issues: list = []
    suggestions: list = []
    score: int = 0
    lint_output: str = ""

app = FastAPI(title="Kod Tahlil Tizimi", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def run_python_lint(code: str) -> str:
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp = f.name
        result = subprocess.run(["python", "-m", "flake8", "--max-line-length=100", tmp], capture_output=True, text=True, timeout=15)
        os.unlink(tmp)
        out = result.stdout.strip()
        if not out: return "✓ Lint xatolari topilmadi"
        cleaned = []
        for line in out.split("\n"):
            parts = line.split(":")
            cleaned.append(":".join(parts[1:]).strip() if len(parts) >= 4 else line)
        return "\n".join(cleaned)
    except subprocess.TimeoutExpired: return "⚠ Lint vaqt chegarasidan oshdi"
    except FileNotFoundError: return "⚠ Flake8 o'rnatilmagan"
    except Exception as e: return f"⚠ Lint xatosi: {e}"

def build_prompt(request: AnalyzeRequest, lint_output: str) -> str:
    parts = [f"Dasturlash tili: {request.language.upper()}", f"Vazifa: {TASK_PROMPTS[request.task]}"]
    if request.instruction and request.instruction.strip():
        parts.append(f"Qo'shimcha ko'rsatma: {request.instruction.strip()}")
    if lint_output and "✓" not in lint_output and "⚠" not in lint_output:
        parts.append(f"Lint natijasi:\n{lint_output}")
    parts.append(f"Kod:\n```{request.language}\n{request.code}\n```")
    return "\n\n".join(parts)

def parse_ai(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            r = json.loads(m.group())
            return {"fixed_code": str(r.get("fixed_code","")), "explanation": str(r.get("explanation","")),
                    "issues": list(r.get("issues",[])), "suggestions": list(r.get("suggestions",[])),
                    "score": max(0, min(100, int(r.get("score", 50))))}
        except: pass
    return {"fixed_code":"","explanation":text,"issues":[],"suggestions":[],"score":0}

async def call_ai(request: AnalyzeRequest, lint_output: str) -> dict:
    if not OPENAI_API_KEY:
        raise HTTPException(500, "OpenAI API kaliti sozlanmagan. .env faylida OPENAI_API_KEY ni belgilang.")
    payload = {"model": "gpt-4o-mini", "messages": [{"role":"system","content":SYSTEM_PROMPT},
               {"role":"user","content":build_prompt(request, lint_output)}],
               "temperature": 0.2, "max_tokens": 3000, "response_format": {"type":"json_object"}}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}, json=payload)
    if resp.status_code != 200:
        raise HTTPException(502, f"AI xizmati xatosi: {resp.status_code} - {resp.text[:200]}")
    data = resp.json()
    return parse_ai(data["choices"][0]["message"]["content"])

@app.get("/")
async def root():
    return {"name": "Kod Tahlil Tizimi API", "version": "1.0.0", "docs": "/docs"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "ai_configured": bool(OPENAI_API_KEY), "languages": SUPPORTED_LANGUAGES, "tasks": list(TASK_PROMPTS.keys())}

@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    lint_output = run_python_lint(request.code) if request.language == "python" else ""
    result = await call_ai(request, lint_output)
    return AnalyzeResponse(fixed_code=result["fixed_code"], explanation=result["explanation"],
        issues=result["issues"], suggestions=result["suggestions"], score=result["score"], lint_output=lint_output)
