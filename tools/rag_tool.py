import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config import CHROMA_DB_PATH, DOCUMENTS_PATH


# 🔥 Better embedding model (same, stable)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def load_documents_to_db():
    print("\n📂 Loading documents into vector DB...")

    all_docs = []
    pdf_files = [f for f in os.listdir(DOCUMENTS_PATH) if f.endswith(".pdf")]

    if not pdf_files:
        print("  ⚠️ No PDFs found")
        return None

    for pdf_file in pdf_files:
        path = os.path.join(DOCUMENTS_PATH, pdf_file)
        print(f"  📄 Loading: {pdf_file}")
        loader = PyPDFLoader(path)
        docs = loader.load()
        all_docs.extend(docs)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300
    )

    chunks = splitter.split_documents(all_docs)

    print(f"  ✅ {len(chunks)} chunks created")

    db = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=CHROMA_DB_PATH
    )

    print(f"  ✅ Stored in ChromaDB")
    return db


def search_documents(query: str, top_k: int = 6) -> str:
    print(f"\n📚 Searching documents for: {query}")

    if not os.path.exists(CHROMA_DB_PATH):
        return "No documents loaded."

    db = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings
    )

    queries = [
        query,
        f"{query} revenue",
        f"{query} profit margin",
        f"{query} financial results",
    ]

    results = []

    for q in queries:
        docs = db.similarity_search(q, k=top_k)
        results.extend(docs)

    # 🔥 Remove duplicates
    unique_docs = []
    seen = set()

    for doc in results:
        content = doc.page_content.strip()
        if content not in seen:
            seen.add(content)
            unique_docs.append(doc)

    if not unique_docs:
        return "No relevant content found."

    # 🔥 ──────────────────────────────────────────────────────
    # 🔥 NEW: PDF RELEVANCE FILTER
    # 🔥 Only keep documents that match the query topic
    # 🔥 ──────────────────────────────────────────────────────
    query_lower = query.lower()
    
    # Define sector-specific keywords
    pharma_keywords = ["pharma", "drug", "fda", "clinical", "biotech", "medicine",
                       "sun pharma", "dr reddy", "cipla", "lupin", "divi", "aurobindo",
                       "zydus", "biosimilar", "generic", "vaccine", "therapy"]
    
    it_keywords = ["tcs", "infosys", "wipro", "hcl", "tech mahindra", "ltimindtree",
                   "mphasis", "it services", "software", "digital", "cloud", "ai services",
                   "consulting", "outsourcing"]
    
    # Detect query type
    is_pharma_query = any(kw in query_lower for kw in pharma_keywords)
    is_it_query = any(kw in query_lower for kw in it_keywords)
    
    relevant_docs = []
    for doc in unique_docs:
        source_name = os.path.basename(doc.metadata.get("source", "")).lower()
        content_lower = doc.page_content.lower()[:500]
        
        # Check if document is relevant to query sector
        doc_is_pharma = any(kw in source_name or kw in content_lower for kw in pharma_keywords)
        doc_is_it = any(kw in source_name or kw in content_lower for kw in it_keywords)
        
        # Keep doc if it matches query sector OR if we can't determine query sector
        if is_pharma_query and doc_is_pharma:
            relevant_docs.append(doc)
        elif is_it_query and doc_is_it:
            relevant_docs.append(doc)
        elif not is_pharma_query and not is_it_query:
            # Generic query - keep all
            relevant_docs.append(doc)
    
    # Fallback: if no relevant docs, return empty (don't pollute with wrong data)
    if not relevant_docs and (is_pharma_query or is_it_query):
        print(f"  ⚠️ No PDF documents relevant to this query — skipping RAG")
        return "No relevant documents found for this query topic. Using web search and API data only."
    
    if not relevant_docs:
        relevant_docs = unique_docs  # fallback to all if no filter applied
    
    # 🔥 ──────────────────────────────────────────────────────

    formatted = f"\n📚 DOCUMENT FINDINGS (filtered for relevance)\n"
    formatted += "=" * 50 + "\n"

    for i, doc in enumerate(relevant_docs[:8], 1):
        source = os.path.basename(doc.metadata.get("source", "Unknown"))
        page = doc.metadata.get("page", "?")

        formatted += f"\n[{i}] {source} | Page {page}\n"
        formatted += f"{doc.page_content}\n"
        formatted += "-" * 50

    print(f"  ✅ Returning {len(relevant_docs)} RELEVANT chunks (filtered from {len(unique_docs)} total)")
    return formatted