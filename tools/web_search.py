from tavily import TavilyClient
from config import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY)

def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Searches the web using Tavily and returns results.
    Each result has: title, url, content
    """
    print(f"\n🔍 Searching: {query}")

    response = client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced"
    )

    results = []
    for r in response["results"]:
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")
        })
        print(f"  ✅ Found: {r.get('title', '')}")

    return results


def format_results(results: list[dict]) -> str:
    """
    Converts results list into clean readable string for LLM.
    """
    formatted = ""
    for i, r in enumerate(results, 1):
        formatted += f"\n[{i}] {r['title']}\n"
        formatted += f"URL: {r['url']}\n"
        formatted += f"{r['content'][:500]}\n"
        formatted += "-" * 40
    return formatted