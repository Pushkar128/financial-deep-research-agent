# Financial Deep Research Agent

A multi-agent AI system that conducts deep, autonomous financial research — similar to how Claude's Deep Research or OpenAI's research mode works, but specialized entirely for financial analysis.

Built as part of an internship assignment for Senda.

---

## What This Does

You type a financial question. The system thinks, plans, researches across multiple sources, and gives you a comprehensive report.

Example queries:
- "Analyze TCS and Infosys revenue performance"
- "Research Sun Pharma drug pipeline and financial outlook"
- "Compare Indian IT sector companies"
- "Deep dive into pharma sector trends 2024"

Ask it for a pasta recipe and it'll politely refuse.

---

## How It Works
You ask a question ↓ System figures out: IT sector or Pharma sector? ↓ Creates a research plan and shows it to you ↓ You approve it ↓ Agent searches the web 10-15 times Each search builds on what it found before ↓ Pulls real stock prices and financial data from APIs ↓ Writes a full research report → saves as .md file

text


The key difference from just asking ChatGPT — it doesn't answer from memory. It actually searches the web live, pulls real financial data, and each step informs the next one.

---

## Architecture
financial_deep_research_agent/ │ ├── main.py # Entry point — run this ├── config.py # Settings and API keys │ ├── agents/ │ ├── router.py # Detects IT or Pharma from the query │ └── planner.py # Creates research plan before executing │ ├── graphs/ │ ├── it_research_graph.py # LangGraph research loop for IT sector │ └── pharma_research_graph.py # LangGraph research loop for Pharma sector │ ├── tools/ │ ├── web_search.py # Tavily web search │ ├── financial_api.py # yfinance — real stock and financial data │ ├── calculator.py # Accurate financial calculations │ └── rag_tool.py # Search uploaded PDF annual reports │ └── data/ └── documents/ # Drop PDF annual reports here

text


---

## Tech Stack

| Component | Tool |
|---|---|
| Agent Framework | LangGraph |
| LLM | OpenRouter free models + Google Gemini (backup) |
| Web Search | Tavily API |
| Financial Data | yfinance |
| Document Search | ChromaDB + HuggingFace Embeddings |
| Calculations | Python |

---

## Setup

Step 1 — Create virtual environment

python -m venv venv
.\venv\Scripts\Activate.ps1

Step 2 — Install dependencies:

pip install -r requirements.txt

Step 3 — Create .env file:

env

OPENROUTER_API_KEY=your_openrouter_key
TAVILY_API_KEY=your_tavily_key
GEMINI_API_KEY=your_gemini_key
Get keys from:

OpenRouter: https://openrouter.ai (free)
Tavily: https://tavily.com (1000 free credits/month)
Gemini: https://aistudio.google.com/apikey (free)


Step 4 — Run:

python main.py