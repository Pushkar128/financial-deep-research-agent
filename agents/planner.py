from agents.router import invoke_with_fallback

def create_research_plan(user_query: str, sector: str) -> dict:
    """
    Takes user query + sector and creates a detailed research plan.
    Shows user WHAT will be researched BEFORE starting.
    """
    print(f"\n📋 Creating research plan for: '{user_query}'")

    prompt = f"""
You are a senior financial research analyst.

A user wants deep research on: "{user_query}"
Sector: {sector}

Create a detailed research plan. Include:
1. Research Objective (1-2 lines)
2. Key Questions to Answer (4-5 questions)
3. Research Steps (6-8 specific steps in order)
4. Data Sources to Use (web search, financial data, documents)
5. Expected Output Structure (what sections the final report will have)

Be specific. Use actual company names, metrics, and financial terms relevant to {sector} sector.
Format clearly with numbered lists.
IMPORTANT: Output ONLY the research plan. No JSON. No extra instructions. No meta-commentary. Plain text only.
"""

    plan_text = invoke_with_fallback(prompt)

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


def get_user_approval(plan: dict) -> bool:
    """
    Shows plan to user and asks for approval.
    Returns True if approved, False if rejected.
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