import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config import CHROMA_DB_PATH, DOCUMENTS_PATH

# Embedding model (free, runs locally — no API needed)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def load_documents_to_db():
    """
    Reads all PDFs from data/documents/ folder
    and stores them in ChromaDB vector database.
    Run this once whenever you add new PDFs.
    """
    print("\n📂 Loading documents into vector DB...")

    all_docs = []
    pdf_files = [f for f in os.listdir(DOCUMENTS_PATH) if f.endswith(".pdf")]

    if not pdf_files:
        print("  ⚠️ No PDFs found in data/documents/ folder")
        return None

    for pdf_file in pdf_files:
        path = os.path.join(DOCUMENTS_PATH, pdf_file)
        print(f"  📄 Loading: {pdf_file}")
        loader = PyPDFLoader(path)
        docs = loader.load()
        all_docs.extend(docs)

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(all_docs)
    print(f"  ✅ {len(chunks)} chunks created from {len(pdf_files)} PDFs")

    # Store in ChromaDB
    db = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=CHROMA_DB_PATH
    )
    print(f"  ✅ Stored in ChromaDB at {CHROMA_DB_PATH}")
    return db


def search_documents(query: str, top_k: int = 4) -> str:
    """
    Searches the vector DB for relevant content based on query.
    Returns formatted string of relevant chunks.
    """
    print(f"\n📚 Searching documents for: {query}")

    # Check if DB exists
    if not os.path.exists(CHROMA_DB_PATH):
        return "⚠️ No documents loaded yet. Add PDFs to data/documents/ and run load_documents_to_db() first."

    db = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings
    )

    results = db.similarity_search(query, k=top_k)

    if not results:
        return "No relevant content found in documents."

    formatted = f"\n📚 Document Search Results for: '{query}'\n"
    formatted += "=" * 40 + "\n"

    for i, doc in enumerate(results, 1):
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "?")
        formatted += f"\n[{i}] Source: {os.path.basename(source)} | Page: {page}\n"
        formatted += f"{doc.page_content[:400]}\n"
        formatted += "-" * 40

    print(f"  ✅ Found {len(results)} relevant chunks")
    return formatted