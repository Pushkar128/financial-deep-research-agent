from agents.router import invoke_with_fallback

def create_research_plan(user_query: str, sector: str) -> dict:
    """
    Takes user query + sector and creates a detailed research plan.
    """
    print(f"\n📋 Creating research plan for: '{user_query}'")

    prompt = f"""You are a senior financial research analyst at a top investment firm.

TASK: Create a detailed research plan for this financial query.

Query: "{user_query}"
Sector: {sector}

You MUST output a complete research plan with these EXACT 5 sections:

1. RESEARCH OBJECTIVE
(Write 1-2 lines about what we want to achieve)

2. KEY QUESTIONS TO ANSWER
(List 4-5 specific financial questions)
- Question 1
- Question 2
- Question 3
- Question 4

3. RESEARCH STEPS
(List 6-8 specific steps in order)
Step 1: ...
Step 2: ...
Step 3: ...

4. DATA SOURCES
- Web search via Tavily
- Financial data via yfinance API
- Annual report PDFs via RAG

5. EXPECTED OUTPUT STRUCTURE
- Executive Summary
- Market Overview
- Company Analysis
- Financial Performance
- Key Trends
- Risks
- Recommendations

Use real company names like TCS, Infosys, Sun Pharma, Dr Reddy's based on sector.
Be specific with financial metrics like revenue, profit margin, ROE, EPS.

DO NOT output JSON. DO NOT output safety messages. DO NOT add meta-commentary.
Output ONLY the 5-section plan as plain text.
"""

    plan_text = invoke_with_fallback(prompt)

    # 🔥 BUG FIX — Validate plan output
    if not plan_text or len(plan_text) < 100 or "safety" in plan_text.lower()[:50]:
        print("  ⚠️ Invalid plan received, generating fallback plan...")
        plan_text = generate_fallback_plan(user_query, sector)

    print("  ✅ Research plan created")
    print("\n" + "="*50)
    print("📋 RESEARCH PLAN:")
    print("="*50)
    print(plan_text)
    print("="*50)

    return {
        "plan_text": plan_text,
        "query": user_query,
        "sector": sector
    }


def generate_fallback_plan(query: str, sector: str) -> str:
    """
    Fallback plan if LLM fails to generate proper output.
    """
    companies = "TCS, Infosys, Wipro, HCL Technologies" if sector == "IT" else "Sun Pharma, Dr Reddy's, Cipla, Lupin"
    
    return f"""
1. RESEARCH OBJECTIVE
Conduct comprehensive financial research on: {query}
Focus on {sector} sector companies and provide actionable insights.

2. KEY QUESTIONS TO ANSWER
- What are the latest revenue figures and growth trends?
- How does profitability compare across companies?
- What are the key market dynamics affecting the sector?
- What are the major risks and opportunities?
- What is the future outlook for the sector?

3. RESEARCH STEPS
Step 1: Initial broad web search on {sector} sector trends
Step 2: Fetch financial data for {companies}
Step 3: Search PDF annual reports for verified financials
Step 4: Deep dive into revenue breakdown by geography
Step 5: Analyze profit margins and ROE comparisons
Step 6: Research competitive positioning and market share
Step 7: Identify risks and regulatory challenges
Step 8: Compile forward-looking recommendations

4. DATA SOURCES
- Web search via Tavily API for latest news
- Financial data via yfinance for stock metrics
- Annual report PDFs via ChromaDB RAG
- Cross-verified revenue from official disclosures

5. EXPECTED OUTPUT STRUCTURE
- Executive Summary
- Market Overview  
- Company Analysis
- Financial Performance
- Key Trends and Insights
- Risks and Challenges
- Outlook and Recommendations
"""


def get_user_approval(plan: dict) -> bool:
    """
    Shows plan to user and asks for approval.
    """
    print("\n" + "="*50)
    print("❓ Do you want to proceed with this research plan?")
    print("   Type 'yes' to start research")
    print("   Type 'no' to cancel")
    print("="*50)

    while True:
        user_input = input("\nYour choice: ").strip().lower()
        if user_input in ["yes", "y"]:
            print("✅ Plan approved! Starting deep research...")
            return True
        elif user_input in ["no", "n"]:
            print("❌ Research cancelled.")
            return False
        else:
            print("Please type 'yes' or 'no'")