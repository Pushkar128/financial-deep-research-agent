from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from datetime import datetime
from agents.router import invoke_with_fallback
from tools.web_search import web_search, format_results
from tools.financial_api import get_stock_info, format_stock_info
from tools.calculator import summarize_metrics, format_metrics
from tools.rag_tool import search_documents
from config import MAX_SEARCH_LOOPS, MIN_SEARCH_LOOPS


class ITResearchState(TypedDict):
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


def initial_search(state: ITResearchState) -> dict:
    print(f"\n{'='*50}")
    print(f"🔍 STEP 1: Initial Search")
    print(f"{'='*50}")

    initial_query = f"Indian IT sector {state['query']} 2024 2025"
    results = web_search(initial_query)
    formatted = format_results(results)

    analysis = invoke_with_fallback(f"""
You are a financial research assistant.
Here are web search results about: "{state['query']}"
{formatted}

Extract:
1. List of IT companies mentioned (e.g. TCS, Infosys, Wipro)
2. Key topics/trends found
3. What should be researched NEXT for deeper analysis?
Be specific and concise.
IMPORTANT: Output plain text only. No JSON.
""")

    print(f"\n🧠 Initial Analysis:\n{analysis[:500]}...")

    return {
        "search_count": 1,
        "all_findings": [f"=== INITIAL SEARCH ===\n{formatted}\n\nANALYSIS:\n{analysis}"],
        "current_focus": analysis,
        "companies_found": [],
        "searches_done": [initial_query],
    }


def fetch_financial_data(state: ITResearchState) -> dict:
    print(f"\n{'='*50}")
    print(f"📊 STEP 2: Fetching Financial Data")
    print(f"{'='*50}")

    it_tickers = {
        "tcs": "TCS.NS",
        "infosys": "INFY.NS",
        "wipro": "WIPRO.NS",
        "hcl": "HCLTECH.NS",
        "tech mahindra": "TECHM.NS",
        "ltimindtree": "LTIM.NS",
        "mphasis": "MPHASIS.NS"
    }

    financial_data = []
    companies_found = []

    query_lower = state["query"].lower()
    findings_lower = " ".join(state["all_findings"]).lower()

    for company, ticker in it_tickers.items():
        if company in query_lower or company in findings_lower:
            try:
                info = get_stock_info(ticker)
                metrics = summarize_metrics(info)
                formatted = format_stock_info(info) + format_metrics(metrics)
                financial_data.append(f"=== {company.upper()} FINANCIALS ===\n{formatted}")
                companies_found.append(company.upper())
            except Exception as e:
                print(f"  ⚠️ Could not fetch {company}: {e}")

    if not companies_found:
        print("  📌 No specific companies found — fetching top 3 IT companies")
        for company, ticker in list(it_tickers.items())[:3]:
            try:
                info = get_stock_info(ticker)
                metrics = summarize_metrics(info)
                formatted = format_stock_info(info) + format_metrics(metrics)
                financial_data.append(f"=== {company.upper()} FINANCIALS ===\n{formatted}")
                companies_found.append(company.upper())
            except Exception as e:
                print(f"  ⚠️ Could not fetch {company}: {e}")

    print(f"\n  ✅ Fetched financial data for: {companies_found}")

    return {
        "financial_data": financial_data,
        "companies_found": companies_found,
        "search_count": state["search_count"] + 1,
        "all_findings": state["all_findings"] + [
            f"=== FINANCIAL DATA (all values in ₹ Crores) ===\n" + "\n".join(financial_data)
        ]
    }


def deep_research(state: ITResearchState) -> dict:
    print(f"\n{'='*50}")
    print(f"🔬 STEP {state['search_count'] + 1}: Deep Research Loop")
    print(f"{'='*50}")

    next_query_prompt = f"""
You are a financial research agent doing deep research on: "{state['query']}"
You have done {state['search_count']} searches.

USER'S APPROVED RESEARCH PLAN (follow this as guide):
{state['plan'][:1000]}

Already searched — DO NOT repeat any of these:
{state['searches_done']}

Latest findings:
{state['all_findings'][-1][:800]}

Pick a COMPLETELY DIFFERENT angle not yet covered. Choose from:
- Revenue breakdown by geography or segment
- Competitor comparison and market share
- AI and automation impact on IT services
- Deal wins and order book analysis
- Employee headcount and attrition trends
- Margin analysis and cost structure
- Stock valuation and investor outlook
- Recent acquisitions or partnerships

Return ONLY the search query. Maximum 10 words. No quotes. No special characters.
"""

    next_search_query = invoke_with_fallback(next_query_prompt).strip()
    next_search_query = next_search_query[:300]
    next_search_query = next_search_query.replace('"', '').replace("'", '')

    if next_search_query in state["searches_done"]:
        angles = [
            f"{state['query']} revenue breakdown geography 2024",
            f"Indian IT sector AI automation impact 2025",
            f"TCS Infosys deal wins order book 2024",
            f"IT services margin analysis cost structure",
            f"Indian IT companies acquisitions partnerships 2024",
            f"IT sector attrition headcount trends 2024",
            f"Indian IT stock valuation investor outlook 2025",
        ]
        for angle in angles:
            if angle not in state["searches_done"]:
                next_search_query = angle
                break

    print(f"\n  🎯 Next search query: '{next_search_query}'")
    print(f"  📋 Plan alignment check: Is this query covered in approved plan? Plan snippet: {state['plan'][:200]}")

    results = web_search(next_search_query)
    formatted = format_results(results)
    doc_results = search_documents(next_search_query)

    # 🔥 LLM-based revenue extraction — understands column headers
    if doc_results and len(doc_results) > 100:
        revenue_extraction = invoke_with_fallback(f"""
You are a financial data extractor.

Read this document text and extract ONLY the annual revenue figures in INR crore.
The table has columns like: Fiscal Year, Employees, USD million revenue, INR crore revenue.
Extract ONLY the INR crore revenue column values — not employee count, not USD million.
Revenue values are typically between 50,000 and 2,50,000 crore for large Indian IT companies.
Employee counts look like 3,00,000 or 3,23,578 — do NOT pick these.
USD million values are typically between 8,000 and 25,000 — do NOT pick these.

Document:
{doc_results[:3000]}

Output ONLY in this exact format, one line per year, nothing else:
FY2024: 153670
FY2025: 162990

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
You are a financial research analyst.

CRITICAL DATA PRIORITY RULES:
1. If Document Results contain financial numbers (revenue, profit, margins), ALWAYS trust them FIRST.
2. Priority order: Document Results > Web Search Results > Financial API data.
3. NEVER use suspicious or very small revenue numbers if Document data exists.
4. If Document Results provide revenue, IGNORE conflicting API values completely.
5. If VERIFIED INR REVENUE block exists at the top, use ONLY those values for revenue.
6. Do NOT use any other revenue figures if VERIFIED block is present.
7. Ignore USD million values entirely — they are a different unit from INR crore.
8. DO NOT change, round, estimate, or recalculate any number from the document.
9. DO NOT convert USD to INR — the INR crore values are already in the VERIFIED block.
10. Use values exactly as written. No interpretation of units.

Research topic: "{state['query']}"
Current search: "{next_search_query}"

Web Search Results:
{formatted[:1500]}

Document Results (FULL PDF CONTEXT - USE EXACT VALUES):
{doc_results}

Summarize the KEY financial insights found. Focus on numbers, percentages, growth rates.
Be specific and data-driven. 3-5 sentences.
IMPORTANT: Output plain text only. No JSON.
""")

    print(f"\n  📝 Findings: {analysis[:200]}...")

    return {
        "search_count": state["search_count"] + 1,
        "searches_done": state["searches_done"] + [next_search_query],
        "all_findings": state["all_findings"] + [
            f"=== SEARCH {state['search_count'] + 1}: {next_search_query} ===\n{formatted[:1000]}\n\nINSIGHTS:\n{analysis}"
        ],
        "current_focus": next_search_query
    }


def write_report(state: ITResearchState) -> dict:
    print(f"\n{'='*50}")
    print(f"📄 Writing Final Report...")
    print(f"{'='*50}")

    all_research = "\n\n".join(state["all_findings"])
    financial = "\n\n".join(state["financial_data"]) if state["financial_data"] else "No financial data"

    report = invoke_with_fallback(f"""
You are a senior financial analyst writing a comprehensive research report.

CRITICAL DATA PRIORITY RULES:
1. Document findings are the PRIMARY source of truth for all financial figures.
2. Priority order: Document Data > Web Search > Financial API.
3. NEVER use small or unrealistic revenue values if document shows a higher correct value.
4. If revenue appears inconsistent across sources, always use document-based numbers.
5. If "VERIFIED INR REVENUE" section exists anywhere in findings, use ONLY those values for revenue.
6. Do NOT use any other revenue numbers from web or API if VERIFIED block exists.
7. Do NOT convert USD million to INR crore — use the INR crore value directly from document.
8. All monetary values in the report must be in ₹ Crores only.

Research Query: "{state['query']}"
Companies Researched: {state['companies_found']}
Total Research Steps: {state['search_count']}

IMPORTANT: All revenue and market cap figures are in ₹ CRORES.

FINANCIAL DATA (secondary — use only if no document data available):
{financial}

ALL RESEARCH FINDINGS (primary source — use these first):
{all_research}

Write a comprehensive financial research report in Markdown format with these sections:

# [Report Title]
## Executive Summary
## Market Overview
## Company Analysis
## Financial Performance
## Key Trends and Insights
## Risks and Challenges
## Outlook and Recommendations

Rules:
- Use ONLY verified financial values from document findings
- For revenue, use VERIFIED INR REVENUE values if present in findings
- NEVER generate, estimate, or infer financial numbers not present in findings
- DO NOT misinterpret units — USD million and INR crore are completely different
- COPY values exactly as found in document-based findings
- All monetary values in ₹ Crores
- Per share values (EPS, dividend) must be written as ₹X per share — never as ₹X crore
- Minimum 1000 words
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


def should_continue(state: ITResearchState) -> str:
    if state["search_count"] >= MAX_SEARCH_LOOPS:
        print(f"\n  ✅ Reached max searches ({MAX_SEARCH_LOOPS}). Writing report...")
        return "write_report"
    elif state["search_count"] < MIN_SEARCH_LOOPS:
        print(f"\n  🔄 Only {state['search_count']} searches done. Need more...")
        return "deep_research"
    else:
        check = invoke_with_fallback(f"""
Research topic: "{state['query']}"
Searches done: {state['search_count']}
Latest finding: {state['all_findings'][-1][:300]}

Do we have ENOUGH information to write a comprehensive financial report?
Answer ONLY: YES or NO
""").strip().upper()

        print(f"\n  🤔 Enough research? LLM says: {check}")
        if "YES" in check:
            return "write_report"
        else:
            return "deep_research"


def build_it_graph():
    graph = StateGraph(ITResearchState)
    graph.add_node("initial_search", initial_search)
    graph.add_node("fetch_financial_data", fetch_financial_data)
    graph.add_node("deep_research", deep_research)
    graph.add_node("write_report", write_report)

    graph.add_edge(START, "initial_search")
    graph.add_edge("initial_search", "fetch_financial_data")
    graph.add_edge("fetch_financial_data", "deep_research")
    graph.add_conditional_edges(
        "deep_research",
        should_continue,
        {
            "deep_research": "deep_research",
            "write_report": "write_report"
        }
    )
    graph.add_edge("write_report", END)
    return graph.compile()


def run_it_research(query: str, plan: str = "") -> str:
    print(f"\n🚀 Starting IT Deep Research Agent")
    print(f"Query: {query}")

    app = build_it_graph()

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
    filename = f"report_IT_{query[:20].replace(' ', '_')}_{timestamp}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(result["report"])

    print(f"\n✅ Report saved to: {filename}")
    print(f"📊 Total searches done: {result['search_count']}")

    return result["report"]