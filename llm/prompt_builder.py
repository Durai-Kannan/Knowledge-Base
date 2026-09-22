def build_rag_prompt(query: str, retrieved_chunks: list[dict]) -> str:
    """
    Constructs a grounded RAG prompt for Gemini LLM using retrieved context chunks.
    """
    context_blocks = []
    for idx, chunk in enumerate(retrieved_chunks, 1):
        url = chunk.get('url', 'N/A')
        title = chunk.get('title', 'N/A')
        content = chunk.get('content', '')
        context_blocks.append(
            f"--- Context Source [{idx}] ---\n"
            f"Title: {title}\n"
            f"URL: {url}\n"
            f"Content: {content}\n"
        )

    context_str = "\n".join(context_blocks) if context_blocks else "No relevant knowledge base content retrieved."

    prompt = f"""You are an expert Executive Intelligence & Knowledge Base Assistant.
Your task is to answer the user's query using ONLY the provided context snippets harvested from leadership webpages.

STRICT RULES:
1. Base your answer strictly on the provided Context Sources below.
2. Do NOT use external or unmentioned information.
3. If the provided context does not contain sufficient details to answer the query, clearly state: "The requested information was not found in the harvested knowledge base."
4. Structure your response clearly using the following markdown format:

### Executive / Person Profile
- **Person / Subject**: [Name or N/A]
- **Current Role**: [Job Title / Position]
- **Organization**: [Company / Institution Name]

### Overview & Biography
[Detailed summary answering the query based on the context]

### Source Citations
- List the exact source URLs used in your response (e.g., [Source Title](URL)).

---
CONTEXT SOURCES:
{context_str}

---
USER QUERY:
{query}
"""
    return prompt
