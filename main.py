import os
from agents.router import route_query
from agents.planner import create_research_plan, get_user_approval
from graphs.it_research_graph import run_it_research
from graphs.pharma_research_graph import run_pharma_research
from tools.rag_tool import load_documents_to_db, DOCUMENTS_PATH


def auto_load_documents():
    """
    Automatically loads PDFs from data/documents/ on startup.
    No manual terminal command needed.
    """
    if os.path.exists(DOCUMENTS_PATH):
        pdf_files = [f for f in os.listdir(DOCUMENTS_PATH) if f.endswith(".pdf")]
        if pdf_files:
            print(f"\n📂 Found {len(pdf_files)} PDF(s) in documents folder. Auto-loading...")
            load_documents_to_db()
        else:
            print("\n📂 No PDFs found in data/documents/ — RAG skipped")
    else:
        print("\n📂 Documents folder not found — RAG skipped")


def main():
    print("\n" + "="*50)
    print("🚀 SENDA FINANCIAL DEEP RESEARCH AGENT")
    print("="*50)

    # Auto load documents — no manual command needed
    auto_load_documents()

    user_query = input("\nEnter your financial research query: ").strip()

    if not user_query:
        print("❌ Error: Query cannot be empty.")
        return

    # 1. ROUTE
    route = route_query(user_query)

    if not route["is_valid"]:
        print(f"\n❌ Sorry, I can only answer finance-related questions.")
        print(f"   Reason: {route['reason']}")
        return

    sector = route["sector"]

    if sector == "UNKNOWN":
        print(f"\n⚠️ Sector not supported yet. Currently supporting IT and PHARMA only.")
        return

    # 2. PLAN
    plan = create_research_plan(user_query, sector)

    # 3. APPROVE
    if not get_user_approval(plan):
        return

    # 4. EXECUTE
    if sector == "IT":
        report = run_it_research(user_query, plan["plan_text"])
    elif sector == "PHARMA":
        report = run_pharma_research(user_query, plan["plan_text"])

    print("\n" + "="*50)
    print("✅ MISSION ACCOMPLISHED")
    print("📄 Report saved to your folder.")
    print("="*50)


if __name__ == "__main__":
    main()