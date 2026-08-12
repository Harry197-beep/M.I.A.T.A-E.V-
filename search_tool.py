from ddgs import DDGS


def web_search(query, max_results=5):
    """Search the web and return a summary of top results."""
    try:
        results = DDGS().text(query, max_results=max_results)
    except Exception as e:
        return f"Search failed: {e}"

    if not results:
        return "No results found."

    summaries = []
    for r in results:
        summaries.append(
            f"Title: {r.get('title', '?')}\n"
            f"Link: {r.get('href', '?')}\n"
            f"Snippet: {r.get('body', '?')}\n"
        )
    return "\n---\n".join(summaries)


if __name__ == "__main__":
    print(web_search("Stockbit latest news", max_results=3))
