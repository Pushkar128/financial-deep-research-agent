from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from openai import RateLimitError, NotFoundError, APIStatusError
from config import (
    OPENROUTER_API_KEY, LLM_BASE_URL, FREE_MODELS,
    GEMINI_API_KEY, GEMINI_MODEL, SUPPORTED_SECTORS
)
import re


def get_openrouter_llm(model: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        base_url=LLM_BASE_URL,
        api_key=OPENROUTER_API_KEY,
        temperature=0
    )


def get_gemini_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0
    )


def invoke_with_fallback(prompt: str) -> str:
    """
    Priority:
    1. Try all OpenRouter free models
    2. If all fail → use Gemini as backup
    """

    # --- TRY OPENROUTER FIRST ---
    for model in FREE_MODELS:
        try:
            print(f"  🤖 Trying OpenRouter: {model}")
            llm = get_openrouter_llm(model)

            for attempt in range(3):
                response = llm.invoke(prompt)
                content = response.content.strip()

                if len(content) < 2 or content.startswith("<"):
                    print(f"  ⚠️ Garbage output attempt {attempt+1}, retrying...")
                    continue

                print(f"  ✅ Success with OpenRouter: {model}")
                return content

            print(f"  ⚠️ {model} kept returning garbage, trying next...")
            continue

        except (RateLimitError, NotFoundError, APIStatusError) as e:
            print(f"  ⚠️ {model} failed ({e.status_code}), trying next...")
            continue
        except Exception as e:
            print(f"  ⚠️ {model} error: {str(e)[:80]}, trying next...")
            continue

    # --- OPENROUTER FAILED → USE GEMINI BACKUP ---
    print(f"  🔄 All OpenRouter models failed. Switching to Gemini backup...")
    try:
        llm = get_gemini_llm()

        for attempt in range(3):
            response = llm.invoke(prompt)
            content = response.content.strip()

            if len(content) < 2 or content.startswith("<"):
                print(f"  ⚠️ Gemini garbage attempt {attempt+1}, retrying...")
                continue

            print(f"  ✅ Success with Gemini!")
            return content

    except Exception as e:
        print(f"  ❌ Gemini also failed: {str(e)[:80]}")

    return "ERROR: All models failed. Try again later."


def route_query(user_query: str) -> dict:
    print(f"\n🧭 Routing query: '{user_query}'")

    prompt = f"""
You are a STRICT financial query router. Your job is to classify the user's query.

Supported sectors: {SUPPORTED_SECTORS}

STRICT RULES:
1. If the query is DIRECTLY about IT/Technology companies (TCS, Infosys, Wipro, HCL, Tech Mahindra, software, IT services) → return IT
2. If the query is DIRECTLY about Pharma/Healthcare/Medicine/Drugs/Biotech companies (Sun Pharma, Dr Reddy's, Cipla, Lupin, Divi's) → return PHARMA
3. If the query is about food, recipes, cooking, sports, entertainment, travel, personal life, hobbies, weather → return OFF_TOPIC with IS_VALID: NO
4. DO NOT try to convert non-finance queries into finance queries.
5. DO NOT interpret "pasta recipe" as "pasta industry analysis" — it is OFF_TOPIC.
6. DO NOT interpret cooking/lifestyle queries as CPG sector analysis.
7. Only mark IS_VALID as YES if the user EXPLICITLY asks about financial/business/investment/stock/revenue/company analysis topics.
8. If the query is finance-related but NOT about IT or Pharma → return UNKNOWN with IS_VALID: YES
9. If unsure → return OFF_TOPIC with IS_VALID: NO

EXAMPLES:
- "Give me a pasta recipe" → SECTOR: OFF_TOPIC, IS_VALID: NO
- "Best cricket match" → SECTOR: OFF_TOPIC, IS_VALID: NO
- "Analyze TCS revenue" → SECTOR: IT, IS_VALID: YES
- "Sun Pharma drug pipeline" → SECTOR: PHARMA, IS_VALID: YES
- "Banking sector analysis" → SECTOR: UNKNOWN, IS_VALID: YES

User Query: "{user_query}"

Respond in EXACTLY this format. Each field on a NEW LINE:
SECTOR: <IT/PHARMA/UNKNOWN/OFF_TOPIC>
REASON: <one line reason>
IS_VALID: <YES/NO>
"""

    content = invoke_with_fallback(prompt)
    print(f"  🤖 Raw Response: {content}")

    result = {
        "sector": "UNKNOWN",
        "reason": "",
        "is_valid": False,
        "original_query": user_query
    }

    sector_match = re.search(r"SECTOR:\s*(IT|PHARMA|UNKNOWN|OFF_TOPIC)", content)
    reason_match = re.search(r"REASON:\s*(.+?)(?=IS_VALID|$)", content, re.DOTALL)
    valid_match = re.search(r"IS_VALID:\s*(YES|NO)", content)

    if sector_match:
        result["sector"] = sector_match.group(1).strip()
    if reason_match:
        result["reason"] = reason_match.group(1).strip()
    if valid_match:
        result["is_valid"] = valid_match.group(1).strip() == "YES"

    # 🔥 SAFETY OVERRIDE — Force OFF_TOPIC to be invalid
    if result["sector"] == "OFF_TOPIC":
        result["is_valid"] = False

    print(f"  ✅ Routed to: {result['sector']} | Valid: {result['is_valid']} | Reason: {result['reason']}")
    return result