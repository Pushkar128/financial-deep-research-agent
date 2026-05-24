from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from datetime import datetime
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
    results = web_search(next_search_query)
    doc_results = search_documents(next_search_query)

    analysis = invoke_with_fallback(f"""
Analyze these pharma results for: {next_search_query}

Web Results:
{format_results(results)[:1500]}

Document Results:
{doc_results[:300]}

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

Research Query: "{state['query']}"
Companies Researched: {state['companies_found']}
Total Research Steps: {state['search_count']}

IMPORTANT: All revenue and market cap figures are in ₹ CRORES.

FINANCIAL DATA:
{financial[:2000]}

ALL RESEARCH FINDINGS:
{all_research[:4000]}

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
- Use actual numbers from the research
- All monetary values in ₹ Crores
- Minimum 600 words
- Professional analyst tone
- Plain markdown only. No JSON.
""")

    print("\n✅ Report written!")
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