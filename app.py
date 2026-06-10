import streamlit as st
import os
import shutil
from agents.router import route_query
from agents.planner import create_research_plan
from graphs.it_research_graph import run_it_research
from graphs.pharma_research_graph import run_pharma_research
from tools.rag_tool import load_documents_to_db, DOCUMENTS_PATH

# ── PAGE CONFIG ──────────────────────────────────────────
st.set_page_config(
    page_title="Senda Financial Research Agent",
    page_icon="📊",
    layout="wide"
)

# ── SESSION STATE INIT ───────────────────────────────────
if "stage" not in st.session_state:
    st.session_state.stage = "idle"
if "query" not in st.session_state:
    st.session_state.query = ""
if "plan" not in st.session_state:
    st.session_state.plan = None
if "sector" not in st.session_state:
    st.session_state.sector = None
if "report" not in st.session_state:
    st.session_state.report = None
if "route" not in st.session_state:
    st.session_state.route = None

# ── AUTO LOAD DOCS ───────────────────────────────────────
@st.cache_resource
def auto_load_documents():
    if os.path.exists(DOCUMENTS_PATH):
        pdf_files = [f for f in os.listdir(DOCUMENTS_PATH) if f.endswith(".pdf")]
        if pdf_files:
            load_documents_to_db()

auto_load_documents()

# ── SIDEBAR ──────────────────────────────────────────────
with st.sidebar:
    st.header("📊 Senda Research Agent")
    st.markdown("""
    **How it works:**
    - 🔍 Searches web 10-15 times per query
    - 📊 Pulls real stock & financial data
    - 📚 Reads uploaded annual report PDFs
    - 🤖 LangGraph intelligent research loop
    """)
    st.divider()
    st.header("✅ Supported Sectors")
    st.markdown("- 🖥️ **IT** — TCS, Infosys, Wipro, HCL")
    st.markdown("- 💊 **Pharma** — Sun Pharma, Dr Reddy's, Cipla")
    st.divider()
    st.header("💡 Try These Queries")
    st.code("Analyze TCS and Infosys revenue")
    st.code("Sun Pharma drug pipeline analysis")
    st.code("Compare Indian IT sector companies")
    st.divider()

    # ── UPLOAD PDF ───────────────────────────────────────
    st.header("📂 Upload Annual Report PDF")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded_file:
        os.makedirs(DOCUMENTS_PATH, exist_ok=True)
        save_path = os.path.join(DOCUMENTS_PATH, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✅ {uploaded_file.name} uploaded!")
        with st.spinner("Indexing..."):
            # Clear cache so it re-indexes
            auto_load_documents.clear()
            load_documents_to_db()
        st.success("✅ Indexed and ready!")

    # ── 🔥 NEW: EXISTING PDFs WITH DELETE OPTION ────────
    st.divider()
    st.header("🗂️ Existing PDFs in System")
    if os.path.exists(DOCUMENTS_PATH):
        existing_pdfs = [f for f in os.listdir(DOCUMENTS_PATH) if f.endswith(".pdf")]
        if existing_pdfs:
            for pdf in existing_pdfs:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"📄 {pdf}")
                with col2:
                    if st.button("🗑️", key=f"del_{pdf}", help=f"Delete {pdf}"):
                        # Delete PDF file from folder
                        os.remove(os.path.join(DOCUMENTS_PATH, pdf))
                        # Clear ChromaDB completely to remove embeddings
                        if os.path.exists("./chroma_db"):
                            shutil.rmtree("./chroma_db")
                        # Clear streamlit cache
                        auto_load_documents.clear()
                        # Re-index remaining PDFs
                        remaining = [f for f in os.listdir(DOCUMENTS_PATH) if f.endswith(".pdf")]
                        if remaining:
                            load_documents_to_db()
                        st.success(f"✅ Deleted {pdf}")
                        st.rerun()
        else:
            st.info("No PDFs uploaded yet")

    # ── 🔥 CLEAR ALL BUTTON ──────────────────────────────
    if st.button("🧹 Clear All PDFs & Index", use_container_width=True):
        if os.path.exists(DOCUMENTS_PATH):
            for pdf in os.listdir(DOCUMENTS_PATH):
                if pdf.endswith(".pdf"):
                    os.remove(os.path.join(DOCUMENTS_PATH, pdf))
        if os.path.exists("./chroma_db"):
            shutil.rmtree("./chroma_db")
        auto_load_documents.clear()
        st.success("✅ All PDFs and index cleared!")
        st.rerun()

# ── HEADER ───────────────────────────────────────────────
st.title("📊 Senda Financial Deep Research Agent")
st.markdown("*Autonomous AI agent for deep financial research — powered by LangGraph + Web Search + Financial APIs*")
st.divider()

# ════════════════════════════════════════════════════════
# STAGE: IDLE — show input
# ════════════════════════════════════════════════════════
if st.session_state.stage == "idle":

    col1, col2 = st.columns([3, 1])

    with col1:
        user_query = st.text_input(
            "Enter your financial research query:",
            placeholder="e.g. Analyze TCS and Infosys revenue performance..."
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        start = st.button("🚀 Start Research", type="primary", use_container_width=True)

    if start:
        if not user_query:
            st.warning("⚠️ Please enter a query first.")
        else:
            st.session_state.query = user_query
            st.session_state.stage = "routing"
            st.rerun()

# ════════════════════════════════════════════════════════
# STAGE: ROUTING — detect sector
# ════════════════════════════════════════════════════════
elif st.session_state.stage == "routing":

    st.info(f"🧭 Analyzing query: *{st.session_state.query}*")

    with st.spinner("Detecting sector..."):
        route = route_query(st.session_state.query)

    if not route["is_valid"]:
        st.error(f"❌ Only finance-related queries allowed. ({route['reason']})")
        if st.button("🔁 Try Again"):
            st.session_state.stage = "idle"
            st.rerun()
    elif route["sector"] == "UNKNOWN":
        st.warning("⚠️ Only IT & Pharma sectors supported currently.")
        if st.button("🔁 Try Again"):
            st.session_state.stage = "idle"
            st.rerun()
    else:
        st.session_state.sector = route["sector"]
        st.session_state.route = route
        st.session_state.stage = "planning"
        st.rerun()

# ════════════════════════════════════════════════════════
# STAGE: PLANNING — create research plan
# ════════════════════════════════════════════════════════
elif st.session_state.stage == "planning":

    st.success(f"✅ Sector detected: **{st.session_state.sector}**")
    st.info("📋 Creating research plan...")

    with st.spinner("Building research plan..."):
        plan = create_research_plan(st.session_state.query, st.session_state.sector)

    st.session_state.plan = plan
    st.session_state.stage = "show_plan"
    st.rerun()

# ════════════════════════════════════════════════════════
# STAGE: SHOW PLAN — user approval
# ════════════════════════════════════════════════════════
elif st.session_state.stage == "show_plan":

    st.success(f"✅ Sector: **{st.session_state.sector}**")
    st.subheader("📋 Research Plan")

    # Editable — user can modify before approving
    edited_plan = st.text_area(
        "Review and edit the research plan if needed:",
        value=st.session_state.plan["plan_text"],
        height=400
    )

    # Save edited version back to state
    st.session_state.plan["plan_text"] = edited_plan

    st.markdown("**Do you want to proceed with this research plan?**")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("✅ Approve & Start Research", type="primary", use_container_width=True):
            st.session_state.stage = "running"
            st.rerun()

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.stage = "idle"
            st.session_state.query = ""
            st.session_state.plan = None
            st.rerun()

# ════════════════════════════════════════════════════════
# STAGE: RUNNING — execute research
# ════════════════════════════════════════════════════════
elif st.session_state.stage == "running":

    st.success(f"✅ Sector: **{st.session_state.sector}**")
    st.subheader("🔬 Deep Research in Progress...")
    st.info("This takes 2-3 minutes. The agent is searching the web, pulling financial data, and analyzing findings...")

    progress = st.progress(0)
    status = st.empty()

    status.text("🔍 Starting research loops...")
    progress.progress(10)

    try:
        if st.session_state.sector == "IT":
            status.text("🖥️ Running IT Research Agent...")
            progress.progress(30)
            report = run_it_research(
                st.session_state.query,
                st.session_state.plan["plan_text"]
            )
        else:
            status.text("💊 Running Pharma Research Agent...")
            progress.progress(30)
            report = run_pharma_research(
                st.session_state.query,
                st.session_state.plan["plan_text"]
            )

        progress.progress(100)
        status.text("✅ Research complete!")

        st.session_state.report = report
        st.session_state.stage = "done"
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error during research: {str(e)}")
        if st.button("🔁 Try Again"):
            st.session_state.stage = "idle"
            st.rerun()

# ════════════════════════════════════════════════════════
# STAGE: DONE — show report
# ════════════════════════════════════════════════════════
elif st.session_state.stage == "done":

    st.success("✅ Research Complete!")
    st.subheader("📄 Financial Research Report")
    st.divider()

    st.markdown(st.session_state.report)

    st.divider()

    # Filename input
    default_name = f"report_{st.session_state.sector}_{st.session_state.query[:20].replace(' ', '_')}.md"
    custom_filename = st.text_input(
        "📁 File name (you can change this):",
        value=default_name
    )

    if not custom_filename.endswith(".md"):
        custom_filename += ".md"

    col1, col2 = st.columns([1, 1])

    with col1:
        st.download_button(
            label="⬇️ Download Report",
            data=st.session_state.report,
            file_name=custom_filename,
            mime="text/markdown",
            use_container_width=True
        )

    with col2:
        if st.button("🔁 Start New Research", use_container_width=True):
            st.session_state.stage = "idle"
            st.session_state.query = ""
            st.session_state.plan = None
            st.session_state.report = None
            st.session_state.sector = None
            st.session_state.route = None
            st.rerun()
# import streamlit as st
# import os
# from agents.router import route_query
# from agents.planner import create_research_plan
# from graphs.it_research_graph import run_it_research
# from graphs.pharma_research_graph import run_pharma_research
# from tools.rag_tool import load_documents_to_db, DOCUMENTS_PATH

# # ── PAGE CONFIG ──────────────────────────────────────────
# st.set_page_config(
#     page_title="Senda Financial Research Agent",
#     page_icon="📊",
#     layout="wide"
# )

# # ── SESSION STATE INIT ───────────────────────────────────
# if "stage" not in st.session_state:
#     st.session_state.stage = "idle"
# if "query" not in st.session_state:
#     st.session_state.query = ""
# if "plan" not in st.session_state:
#     st.session_state.plan = None
# if "sector" not in st.session_state:
#     st.session_state.sector = None
# if "report" not in st.session_state:
#     st.session_state.report = None
# if "route" not in st.session_state:
#     st.session_state.route = None

# # ── AUTO LOAD DOCS ───────────────────────────────────────
# @st.cache_resource
# def auto_load_documents():
#     if os.path.exists(DOCUMENTS_PATH):
#         pdf_files = [f for f in os.listdir(DOCUMENTS_PATH) if f.endswith(".pdf")]
#         if pdf_files:
#             load_documents_to_db()

# auto_load_documents()

# # ── SIDEBAR ──────────────────────────────────────────────
# with st.sidebar:
#     st.header("📊 Senda Research Agent")
#     st.markdown("""
#     **How it works:**
#     - 🔍 Searches web 10-15 times per query
#     - 📊 Pulls real stock & financial data
#     - 📚 Reads uploaded annual report PDFs
#     - 🤖 LangGraph intelligent research loop
#     """)
#     st.divider()
#     st.header("✅ Supported Sectors")
#     st.markdown("- 🖥️ **IT** — TCS, Infosys, Wipro, HCL")
#     st.markdown("- 💊 **Pharma** — Sun Pharma, Dr Reddy's, Cipla")
#     st.divider()
#     st.header("💡 Try These Queries")
#     st.code("Analyze TCS and Infosys revenue")
#     st.code("Sun Pharma drug pipeline analysis")
#     st.code("Compare Indian IT sector companies")
#     st.divider()
#     st.header("📂 Upload Annual Report PDF")
#     uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
#     if uploaded_file:
#         os.makedirs(DOCUMENTS_PATH, exist_ok=True)
#         save_path = os.path.join(DOCUMENTS_PATH, uploaded_file.name)
#         with open(save_path, "wb") as f:
#             f.write(uploaded_file.getbuffer())
#         st.success(f"✅ {uploaded_file.name} uploaded!")
#         with st.spinner("Indexing..."):
#             load_documents_to_db()
#         st.success("✅ Indexed and ready!")

# # ── HEADER ───────────────────────────────────────────────
# st.title("📊 Senda Financial Deep Research Agent")
# st.markdown("*Autonomous AI agent for deep financial research — powered by LangGraph + Web Search + Financial APIs*")
# st.divider()

# # ════════════════════════════════════════════════════════
# # STAGE: IDLE — show input
# # ════════════════════════════════════════════════════════
# if st.session_state.stage == "idle":

#     col1, col2 = st.columns([3, 1])

#     with col1:
#         user_query = st.text_input(
#             "Enter your financial research query:",
#             placeholder="e.g. Analyze TCS and Infosys revenue performance..."
#         )

#     with col2:
#         st.markdown("<br>", unsafe_allow_html=True)
#         start = st.button("🚀 Start Research", type="primary", use_container_width=True)

#     if start:
#         if not user_query:
#             st.warning("⚠️ Please enter a query first.")
#         else:
#             st.session_state.query = user_query
#             st.session_state.stage = "routing"
#             st.rerun()

# # ════════════════════════════════════════════════════════
# # STAGE: ROUTING — detect sector
# # ════════════════════════════════════════════════════════
# elif st.session_state.stage == "routing":

#     st.info(f"🧭 Analyzing query: *{st.session_state.query}*")

#     with st.spinner("Detecting sector..."):
#         route = route_query(st.session_state.query)

#     if not route["is_valid"]:
#         st.error(f"❌ Only finance-related queries allowed. ({route['reason']})")
#         if st.button("🔁 Try Again"):
#             st.session_state.stage = "idle"
#             st.rerun()
#     elif route["sector"] == "UNKNOWN":
#         st.warning("⚠️ Only IT & Pharma sectors supported currently.")
#         if st.button("🔁 Try Again"):
#             st.session_state.stage = "idle"
#             st.rerun()
#     else:
#         st.session_state.sector = route["sector"]
#         st.session_state.route = route
#         st.session_state.stage = "planning"
#         st.rerun()

# # ════════════════════════════════════════════════════════
# # STAGE: PLANNING — create research plan
# # ════════════════════════════════════════════════════════
# elif st.session_state.stage == "planning":

#     st.success(f"✅ Sector detected: **{st.session_state.sector}**")
#     st.info("📋 Creating research plan...")

#     with st.spinner("Building research plan..."):
#         plan = create_research_plan(st.session_state.query, st.session_state.sector)

#     st.session_state.plan = plan
#     st.session_state.stage = "show_plan"
#     st.rerun()

# # ════════════════════════════════════════════════════════
# # STAGE: SHOW PLAN — user approval
# # ════════════════════════════════════════════════════════
# elif st.session_state.stage == "show_plan":

#     st.success(f"✅ Sector: **{st.session_state.sector}**")
#     st.subheader("📋 Research Plan")

#     with st.expander("View full research plan", expanded=True):
#         st.markdown(st.session_state.plan["plan_text"])

#     st.markdown("**Do you want to proceed with this research plan?**")

#     col1, col2 = st.columns([1, 1])

#     with col1:
#         if st.button("✅ Approve & Start Research", type="primary", use_container_width=True):
#             st.session_state.stage = "running"
#             st.rerun()

#     with col2:
#         if st.button("❌ Cancel", use_container_width=True):
#             st.session_state.stage = "idle"
#             st.session_state.query = ""
#             st.session_state.plan = None
#             st.rerun()

# # ════════════════════════════════════════════════════════
# # STAGE: RUNNING — execute research
# # ════════════════════════════════════════════════════════
# elif st.session_state.stage == "running":

#     st.success(f"✅ Sector: **{st.session_state.sector}**")
#     st.subheader("🔬 Deep Research in Progress...")
#     st.info("This takes 2-3 minutes. The agent is searching the web, pulling financial data, and analyzing findings...")

#     progress = st.progress(0)
#     status = st.empty()

#     status.text("🔍 Starting research loops...")
#     progress.progress(10)

#     try:
#         if st.session_state.sector == "IT":
#             status.text("🖥️ Running IT Research Agent...")
#             progress.progress(30)
#             report = run_it_research(
#                 st.session_state.query,
#                 st.session_state.plan["plan_text"]
#             )
#         else:
#             status.text("💊 Running Pharma Research Agent...")
#             progress.progress(30)
#             report = run_pharma_research(
#                 st.session_state.query,
#                 st.session_state.plan["plan_text"]
#             )

#         progress.progress(100)
#         status.text("✅ Research complete!")

#         st.session_state.report = report
#         st.session_state.stage = "done"
#         st.rerun()

#     except Exception as e:
#         st.error(f"❌ Error during research: {str(e)}")
#         if st.button("🔁 Try Again"):
#             st.session_state.stage = "idle"
#             st.rerun()
# # ════════════════════════════════════════════════════════
# # STAGE: DONE — show report
# # ════════════════════════════════════════════════════════
# elif st.session_state.stage == "done":

#     st.success("✅ Research Complete!")
#     st.subheader("📄 Financial Research Report")
#     st.divider()

#     st.markdown(st.session_state.report)

#     st.divider()

#     # Filename input
#     default_name = f"report_{st.session_state.sector}_{st.session_state.query[:20].replace(' ', '_')}.md"
#     custom_filename = st.text_input(
#         "📁 File name (you can change this):",
#         value=default_name
#     )

#     # Make sure it ends with .md
#     if not custom_filename.endswith(".md"):
#         custom_filename += ".md"

#     col1, col2 = st.columns([1, 1])

#     with col1:
#         st.download_button(
#             label="⬇️ Download Report",
#             data=st.session_state.report,
#             file_name=custom_filename,
#             mime="text/markdown",
#             use_container_width=True
#         )

#     with col2:
#         if st.button("🔁 Start New Research", use_container_width=True):
#             st.session_state.stage = "idle"
#             st.session_state.query = ""
#             st.session_state.plan = None
#             st.session_state.report = None
#             st.session_state.sector = None
#             st.session_state.route = None
#             st.rerun()
# # ════════════════════════════════════════════════════════
# # STAGE: DONE — show report
# # ════════════════════════════════════════════════════════
# elif st.session_state.stage == "done":

#     st.success("✅ Research Complete!")
#     st.subheader("📄 Financial Research Report")
#     st.divider()

#     st.markdown(st.session_state.report)

#     st.divider()

#     col1, col2 = st.columns([1, 1])

#     with col1:
#         st.download_button(
#             label="⬇️ Download Report (.md)",
#             data=st.session_state.report,
#             file_name=f"report_{st.session_state.sector}_{st.session_state.query[:20].replace(' ', '_')}.md",
#             mime="text/markdown",
#             use_container_width=True
#         )

#     with col2:
#         if st.button("🔁 Start New Research", use_container_width=True):
#             st.session_state.stage = "idle"
#             st.session_state.query = ""
#             st.session_state.plan = None
#             st.session_state.report = None
#             st.session_state.sector = None
#             st.session_state.route = None
#             st.rerun()
# import streamlit as st
# import os
# from agents.router import route_query
# from agents.planner import create_research_plan
# from graphs.it_research_graph import run_it_research
# from graphs.pharma_research_graph import run_pharma_research
# from tools.rag_tool import load_documents_to_db, DOCUMENTS_PATH

# # ── Page Config ──────────────────────────────────────────
# st.set_page_config(
#     page_title="Senda Financial Research Agent",
#     page_icon="📊",
#     layout="wide"
# )

# # ── Auto load PDFs ────────────────────────────────────────
# def auto_load_documents():
#     if os.path.exists(DOCUMENTS_PATH):
#         pdf_files = [f for f in os.listdir(DOCUMENTS_PATH) if f.endswith(".pdf")]
#         if pdf_files:
#             load_documents_to_db()

# auto_load_documents()

# # ── Header ────────────────────────────────────────────────
# st.title("📊 Senda Financial Deep Research Agent")
# st.markdown("*Autonomous AI agent that researches financial queries in depth — powered by LangGraph + Real-time Web Search + Financial APIs*")
# st.divider()

# # ── Sidebar ───────────────────────────────────────────────
# with st.sidebar:
#     st.header("ℹ️ About")
#     st.markdown("""
#     This agent conducts **deep financial research** by:
#     - 🔍 Searching the web 10-15 times per query
#     - 📊 Pulling real stock & financial data
#     - 📚 Reading uploaded annual reports (RAG)
#     - 🤖 Using LangGraph for intelligent research loops
#     """)

#     st.divider()
#     st.header("✅ Supported Sectors")
#     st.markdown("- 🖥️ **IT** — TCS, Infosys, Wipro, HCL")
#     st.markdown("- 💊 **Pharma** — Sun Pharma, Dr Reddy's, Cipla")

#     st.divider()
#     st.header("📂 Upload Annual Reports")
#     uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
#     if uploaded_file:
#         os.makedirs(DOCUMENTS_PATH, exist_ok=True)
#         save_path = os.path.join(DOCUMENTS_PATH, uploaded_file.name)
#         with open(save_path, "wb") as f:
#             f.write(uploaded_file.getbuffer())
#         st.success(f"✅ {uploaded_file.name} uploaded!")
#         with st.spinner("Indexing document..."):
#             load_documents_to_db()
#         st.success("✅ Document indexed and ready!")

#     st.divider()
#     st.header("💡 Example Queries")
#     st.code("Analyze TCS and Infosys revenue")
#     st.code("Sun Pharma drug pipeline analysis")
#     st.code("Compare Indian IT sector companies")

# # ── Main Input ────────────────────────────────────────────
# col1, col2 = st.columns([3, 1])

# with col1:
#     user_query = st.text_input(
#         "Enter your financial research query:",
#         placeholder="e.g. Analyze TCS and Infosys revenue performance..."
#     )

# with col2:
#     st.markdown("<br>", unsafe_allow_html=True)
#     run_button = st.button("🚀 Start Research", type="primary", use_container_width=True)

# # ── Research Flow ─────────────────────────────────────────
# if run_button and user_query:

#     # Step 1: Route
#     with st.spinner("🧭 Analyzing query..."):
#         route = route_query(user_query)

#     if not route["is_valid"]:
#         st.error(f"❌ Sorry, I only handle finance-related queries. ({route['reason']})")
#         st.stop()

#     sector = route["sector"]

#     if sector == "UNKNOWN":
#         st.warning("⚠️ Currently supporting IT and PHARMA sectors only.")
#         st.stop()

#     st.success(f"✅ Sector detected: **{sector}**")

#     # Step 2: Plan
#     with st.spinner("📋 Creating research plan..."):
#         plan = create_research_plan(user_query, sector)

#     st.subheader("📋 Research Plan")
#     with st.expander("Click to view full research plan", expanded=True):
#         st.markdown(plan["plan_text"])

#     # Step 3: Approve
#     col_yes, col_no, col_empty = st.columns([1, 1, 4])
#     with col_yes:
#         approve = st.button("✅ Approve & Start", type="primary")
#     with col_no:
#         reject = st.button("❌ Cancel")

#     if reject:
#         st.info("Research cancelled.")
#         st.stop()

#     if approve:
#         # Step 4: Research
#         st.subheader("🔬 Research in Progress...")
#         progress_bar = st.progress(0)
#         status_text = st.empty()

#         status_text.text("🔍 Starting deep research...")
#         progress_bar.progress(10)

#         with st.spinner(f"Running {sector} deep research agent (this takes 2-3 minutes)..."):
#             if sector == "IT":
#                 status_text.text("🔍 Researching IT sector...")
#                 progress_bar.progress(30)
#                 report = run_it_research(user_query, plan["plan_text"])
#             elif sector == "PHARMA":
#                 status_text.text("💊 Researching Pharma sector...")
#                 progress_bar.progress(30)
#                 report = run_pharma_research(user_query, plan["plan_text"])

#         progress_bar.progress(100)
#         status_text.text("✅ Research complete!")

#         # Step 5: Show Report
#         st.divider()
#         st.subheader("📄 Research Report")
#         st.markdown(report)

#         # Download button
#         st.download_button(
#             label="⬇️ Download Report (.md)",
#             data=report,
#             file_name=f"report_{sector}_{user_query[:20].replace(' ', '_')}.md",
#             mime="text/markdown"
#         )

# elif run_button and not user_query:
#     st.warning("⚠️ Please enter a query first.")