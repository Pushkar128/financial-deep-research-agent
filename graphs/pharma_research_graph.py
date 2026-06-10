from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from datetime import datetime

from numpy import rint
from agents.router import invoke_with_fallback
from tools.web_search import web_search, format_results
from tools.financial_api import get_stock_info, format_stock_info
from tools.calculator import summarize_metrics, format_metrics
from tools.rag_tool import search_documents
from config import MAX_SEARCH_LOOPS, MIN_SEARCH_LOOPS


class PharmaResearchState(TypedDict):
    query: str
    plan: str
    search_count: int
    all_findings: list[str]
    current_focus: str
    companies_found: list[str]
    financial_data: list[str]
    searches_done: list[str]
    report: str
    done: bool


def initial_search(state: PharmaResearchState) -> dict:
    print(f"\n{'='*50}")
    print(f"🔍 STEP 1: Pharma Initial Search")
    print(f"{'='*50}")

    initial_query = f"Indian Pharmaceutical sector {state['query']} 2024 2025 trends"
    results = web_search(initial_query)
    formatted = format_results(results)

    analysis = invoke_with_fallback(f"""
You are a specialized Pharma Research Analyst.
Here are results for: "{state['query']}"
{formatted}

Extract:
1. Pharma companies mentioned (e.g. Sun Pharma, Dr Reddy's, Cipla, Lupin, Divi's)
2. Key drug pipelines or FDA approvals mentioned
3. What clinical or financial details should be researched NEXT?
IMPORTANT: Output plain text only. No JSON.
""")

    print(f"\n🧠 Initial Pharma Analysis:\n{analysis[:500]}...")

    return {
        "search_count": 1,
        "all_findings": [f"=== INITIAL PHARMA SEARCH ===\n{formatted}\n\nANALYSIS:\n{analysis}"],
        "current_focus": analysis,
        "companies_found": [],
        "searches_done": [initial_query],
    }


def fetch_pharma_financials(state: PharmaResearchState) -> dict:
    print(f"\n{'='*50}")
    print(f"📊 STEP 2: Fetching Pharma Financial Data")
    print(f"{'='*50}")

    pharma_tickers = {
        "sun pharma": "SUNPHARMA.NS",
        "dr reddy": "DRREDDY.NS",
        "cipla": "CIPLA.NS",
        "divi": "DIVISLAB.NS",
        "lupin": "LUPIN.NS",
        "aurobindo": "AUROPHARMA.NS",
        "zydus": "ZYDUSLIFE.NS"
    }

    financial_data = []
    companies_found = []

    findings_lower = " ".join(state["all_findings"]).lower()

    for company, ticker in pharma_tickers.items():
        if company in findings_lower or company in state["query"].lower():
            try:
                info = get_stock_info(ticker)
                metrics = summarize_metrics(info)
                formatted = format_stock_info(info) + format_metrics(metrics)
                financial_data.append(f"=== {company.upper()} FINANCIALS ===\n{formatted}")
                companies_found.append(company.upper())
            except Exception:
                continue

    if not companies_found:
        for company, ticker in list(pharma_tickers.items())[:2]:
            try:
                info = get_stock_info(ticker)
                financial_data.append(format_stock_info(info))
                companies_found.append(company.upper())
            except Exception:
                continue

    return {
        "financial_data": financial_data,
        "companies_found": companies_found,
        "search_count": state["search_count"] + 1,
        "all_findings": state["all_findings"] + [
            f"=== FINANCIAL DATA (all values in ₹ Crores) ===\n" + "\n".join(financial_data)
        ]
    }


def deep_research(state: PharmaResearchState) -> dict:
    print(f"\n{'='*50}")
    print(f"🔬 STEP {state['search_count'] + 1}: Pharma Deep Dive")
    print(f"{'='*50}")

    next_query_prompt = f"""
You are a Pharma Analyst researching: "{state['query']}"
Previous findings: {state['all_findings'][-1][:500]}

USER'S APPROVED RESEARCH PLAN (follow this as guide):
{state['plan'][:1000]}

Already searched — DO NOT repeat any of these:
{state['searches_done']}

Pick a COMPLETELY DIFFERENT angle not yet covered. Choose from:
- Drug pipeline clinical trials status
- Revenue breakdown by geography
- Competitor comparison financials
- R&D spending as percentage of revenue
- Recent acquisitions or partnerships
- Regulatory risks and FDA warnings
- Market share trends India vs global

Return ONLY the search query. Maximum 10 words. No quotes. No special characters.
"""

    next_search_query = invoke_with_fallback(next_query_prompt).strip()
    next_search_query = next_search_query[:300]
    next_search_query = next_search_query.replace('"', '').replace("'", '')

    if next_search_query in state["searches_done"]:
        angles = [
            f"{state['query']} revenue breakdown geography 2024",
            f"{state['query']} competitor comparison market share",
            f"{state['query']} acquisitions partnerships 2024",
            f"{state['query']} regulatory risks FDA warnings",
            f"{state['query']} R&D spending innovation pipeline",
            f"Indian pharma sector growth outlook 2025",
            f"pharma sector challenges pricing pressure India",
        ]
        for angle in angles:
            if angle not in state["searches_done"]:
                next_search_query = angle
                break

    print(f"\n  🎯 Next search: '{next_search_query}'")
    print(f"  📋 Plan alignment check: Is this query covered in approved plan? Plan snippet: {state['plan'][:200]}")
    results = web_search(next_search_query)
    formatted = format_results(results)
    doc_results = search_documents(next_search_query)

    # 🔥 LLM-based revenue extraction — understands column headers
    if doc_results and len(doc_results) > 100:
        revenue_extraction = invoke_with_fallback(f"""
You are a financial data extractor.

Read this document text and extract ONLY the annual revenue figures in INR crore.
The table may have columns like: Fiscal Year, Employees, USD million revenue, INR crore revenue.
Extract ONLY the INR crore revenue column values — not employee count, not USD million.
Revenue values for large Indian pharma companies are typically between 5,000 and 1,00,000 crore.
Employee counts like 30,000 or 50,000 — do NOT pick these.
USD million values are typically between 500 and 10,000 — do NOT pick these.

Document:
{doc_results[:3000]}

Output ONLY in this exact format, one line per year, nothing else:
FY2024: 55000
FY2025: 58462

If no INR crore revenue data found, output exactly: NONE
""")

        revenue_extraction = revenue_extraction.strip()

        if revenue_extraction and "NONE" not in revenue_extraction:
            structured_revenue = "=== VERIFIED INR REVENUE (USE ONLY THESE VALUES) ===\n"
            structured_revenue += revenue_extraction + "\n"
            structured_revenue += "=== END VERIFIED REVENUE ===\n"
            doc_results = structured_revenue + "\n\n" + doc_results
            print(f"\n  ✅ Verified INR Revenue injected:\n{structured_revenue}")
        else:
            print(f"\n  ⚠️ No INR revenue found in documents this step")

    analysis = invoke_with_fallback(f"""
You are a pharma financial research analyst.

CRITICAL DATA PRIORITY RULES:
1. If Document Results contain financial numbers, ALWAYS trust them FIRST.
2. Priority order: Document Results > Web Search Results > Financial API data.
3. If VERIFIED INR REVENUE block exists at the top, use ONLY those values for revenue.
4. Do NOT use any other revenue figures if VERIFIED block is present.
5. Ignore USD million values — they are a different unit from INR crore.
6. Use values exactly as written. No interpretation of units.

Research topic: "{state['query']}"
Current search: "{next_search_query}"

Web Results:
{formatted[:1500]}

Document Results (USE EXACT VALUES):
{doc_results}

Summarize KEY financial insights. Focus on numbers, growth rates, company performance.
3-5 sentences. Be specific and data-driven.
IMPORTANT: Output plain text only. No JSON.
""")

    print(f"\n  📝 Findings: {analysis[:200]}...")

    return {
        "search_count": state["search_count"] + 1,
        "searches_done": state["searches_done"] + [next_search_query],
        "all_findings": state["all_findings"] + [
            f"=== DEEP DIVE: {next_search_query} ===\n{analysis}"
        ],
        "current_focus": next_search_query
    }


def write_report(state: PharmaResearchState) -> dict:
    print(f"\n{'='*50}")
    print(f"📄 Writing Pharma Report...")
    print(f"{'='*50}")

    all_research = "\n\n".join(state["all_findings"])
    financial = "\n\n".join(state["financial_data"]) if state["financial_data"] else "No financial data"

    report = invoke_with_fallback(f"""
You are a senior pharmaceutical analyst writing a comprehensive research report.

CRITICAL DATA PRIORITY RULES:
1. Document findings are the PRIMARY source of truth for all financial figures.
2. Priority order: Document Data > Web Search > Financial API.
3. If VERIFIED INR REVENUE section exists in findings, use ONLY those values for revenue.
4. All monetary values in the report must be in ₹ Crores only.
5. Per share values (EPS, dividend) must be written as ₹X per share — never as ₹X crore.

Research Query: "{state['query']}"
Companies Researched: {state['companies_found']}
Total Research Steps: {state['search_count']}

FINANCIAL DATA (secondary):
{financial}

ALL RESEARCH FINDINGS (primary source):
{all_research}

Write a comprehensive financial research report in Markdown format with these sections:

# [Report Title]
## Executive Summary
## Sector Overview and Market Dynamics
## Company Analysis and Drug Pipeline
## Financial Performance
## R&D and Innovation
## Risks and Regulatory Challenges
## Outlook and Recommendations

Rules:
- Use ONLY verified financial values from document findings
- All monetary values in ₹ Crores
- Per share values as ₹X per share
- Minimum 800 words
- Professional analyst tone
- Plain markdown only. No JSON.
""")

    print("\n✅ Report written!")
    print(f"\n📊 RESEARCH SUMMARY:")
    print(f"   Total searches: {state['search_count']}")
    print(f"   Searches done: {state['searches_done']}")
    print(f"   Companies covered: {state['companies_found']}")
    print(f"   Plan was: {state['plan'][:300]}")
    return {"report": report, "done": True}


def should_continue(state: PharmaResearchState) -> str:
    if state["search_count"] >= MAX_SEARCH_LOOPS:
        print(f"\n  ✅ Reached max searches ({MAX_SEARCH_LOOPS}). Writing report...")
        return "write_report"
    if state["search_count"] < MIN_SEARCH_LOOPS:
        print(f"\n  🔄 Only {state['search_count']} searches done. Need more...")
        return "deep_research"

    check = invoke_with_fallback(f"""
Research topic: "{state['query']}"
Searches done: {state['search_count']}
Latest finding: {state['all_findings'][-1][:300]}

Do we have ENOUGH information to write a comprehensive pharma report?
Answer ONLY: YES or NO
""").strip().upper()

    print(f"\n  🤔 Enough research? LLM says: {check}")
    return "write_report" if "YES" in check else "deep_research"


def run_pharma_research(query: str, plan: str = "") -> str:
    print(f"\n🚀 Starting Pharma Deep Research Agent")
    print(f"Query: {query}")

    graph = StateGraph(PharmaResearchState)
    graph.add_node("initial_search", initial_search)
    graph.add_node("fetch_financial_data", fetch_pharma_financials)
    graph.add_node("deep_research", deep_research)
    graph.add_node("write_report", write_report)

    graph.add_edge(START, "initial_search")
    graph.add_edge("initial_search", "fetch_financial_data")
    graph.add_edge("fetch_financial_data", "deep_research")
    graph.add_conditional_edges("deep_research", should_continue, {
        "deep_research": "deep_research",
        "write_report": "write_report"
    })
    graph.add_edge("write_report", END)

    app = graph.compile()
    result = app.invoke({
        "query": query,
        "plan": plan,
        "search_count": 0,
        "all_findings": [],
        "current_focus": query,
        "companies_found": [],
        "financial_data": [],
        "searches_done": [],
        "report": "",
        "done": False
    })

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_PHARMA_{query[:20].replace(' ', '_')}_{timestamp}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(result["report"])

    print(f"\n✅ Report saved to: {filename}")
    print(f"📊 Total searches done: {result['search_count']}")

    return result["report"]