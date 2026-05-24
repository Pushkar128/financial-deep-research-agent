import os
from dotenv import load_dotenv

load_dotenv()

# ==================== API KEYS ====================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ==================== LLM CONFIG ====================
# Primary: OpenRouter (as suggested in assignment)
FREE_MODELS = [
    "openrouter/free",
    "deepseek/deepseek-v4-flash:free",
    "openai/gpt-oss-120b:free",
    "arcee-ai/trinity-large-thinking:free",
    "qwen/qwen3-coder:free",
]

LLM_MODEL = FREE_MODELS[0]
LLM_BASE_URL = "https://openrouter.ai/api/v1"
LLM_TEMPERATURE = 0.3

# Backup: Gemini
GEMINI_MODEL = "gemini-2.5-flash"

# ==================== RESEARCH SETTINGS ====================
MAX_SEARCH_LOOPS = 12
MIN_SEARCH_LOOPS = 5

SUPPORTED_SECTORS = ["IT", "PHARMA"]

CHROMA_DB_PATH = "./chroma_db"
DOCUMENTS_PATH = "./data/documents"

print("✅ Config loaded successfully!")
print(f"📌 Primary: OpenRouter | Backup: Gemini")