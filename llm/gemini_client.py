import os
import time
from typing import Dict, Any, List

from django.conf import settings

from .prompt_builder import build_rag_prompt


def get_gemini_api_key() -> str:
    """
    Get Gemini API key from environment variables or Django settings.
    """
    return (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or getattr(settings, "GEMINI_API_KEY", "")
    )


def generate_rag_answer(
    query: str,
    retrieved_chunks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate a grounded RAG response using Google Gemini.

    Returns:
    {
        'answer': str,
        'model': str,
        'sources': list[dict],
        'success': bool,
        'error': str
    }
    """

    api_key = get_gemini_api_key()

    # ---------------------------------------------------------
    # 1. Build unique source list
    # ---------------------------------------------------------
    sources = []
    seen_urls = set()

    for chunk in retrieved_chunks:
        url = chunk.get("url")

        if url and url not in seen_urls:
            seen_urls.add(url)

            sources.append({
                "url": url,
                "title": chunk.get("title", url),
                "score": chunk.get("score", 0.0),
            })

    # ---------------------------------------------------------
    # 2. No retrieved chunks
    # ---------------------------------------------------------
    if not retrieved_chunks:
        return {
            "answer": (
                "No relevant content was found in the "
                "knowledge base for your query."
            ),
            "model": "none",
            "sources": [],
            "success": False,
            "error": "No matching vector chunks retrieved.",
        }

    # ---------------------------------------------------------
    # 3. Gemini API key missing
    # ---------------------------------------------------------
    if not api_key:
        sources_str = "\n".join(
            [
                f"- [{s['title']}]({s['url']}) "
                f"(Score: {s['score']:.2f})"
                for s in sources
            ]
        )

        context_snippets = "\n\n".join(
            [
                f"**[{c.get('title', 'Untitled')}]**: "
                f"{c.get('content', '')}"
                for c in retrieved_chunks[:3]
            ]
        )

        fallback_msg = (
            "> [!NOTE]\n"
            "> **Gemini API Key missing**: "
            "`GEMINI_API_KEY` is not configured.\n\n"
            f"### Retrieved Context "
            f"({len(retrieved_chunks)} chunks found):\n\n"
            f"{context_snippets}\n\n"
            "### Sources:\n"
            f"{sources_str}"
        )

        return {
            "answer": fallback_msg,
            "model": "faiss-fallback",
            "sources": sources,
            "success": True,
            "error": "GEMINI_API_KEY missing.",
        }

    # ---------------------------------------------------------
    # 4. Build RAG prompt
    # ---------------------------------------------------------
    prompt = build_rag_prompt(
        query,
        retrieved_chunks
    )

    # ---------------------------------------------------------
    # 5. Gemini configuration
    # ---------------------------------------------------------
    model_name = "gemini-3-flash-preview"

    # Retry only temporary failures.
    max_retries = 3

    try:
        from google import genai

        client = genai.Client(
            api_key=api_key
        )

        # -----------------------------------------------------
        # 6. Generate Gemini response with retry
        # -----------------------------------------------------
        for attempt in range(max_retries):

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )

                if not response:
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                answer = getattr(
                    response,
                    "text",
                    None
                )

                if not answer:
                    raise RuntimeError(
                        "Gemini response contained no text."
                    )

                # Successful response
                return {
                    "answer": answer,
                    "model": model_name,
                    "sources": sources,
                    "success": True,
                    "error": "",
                }

            except Exception as e:

                error_text = str(e)

                is_503 = (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                )

                is_429 = (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                )

                # -------------------------------------------------
                # Temporary service problem
                # -------------------------------------------------
                if is_503:

                    if attempt < max_retries - 1:

                        wait_time = 2 ** attempt

                        print(
                            f"Gemini returned 503. "
                            f"Retrying in {wait_time} seconds..."
                        )

                        time.sleep(wait_time)
                        continue

                    return {
                        "answer": (
                            "Gemini is temporarily experiencing "
                            "high demand. Please try again "
                            "in a few moments."
                        ),
                        "model": model_name,
                        "sources": sources,
                        "success": False,
                        "error": (
                            f"Gemini API temporarily unavailable: "
                            f"{error_text}"
                        ),
                    }

                # -------------------------------------------------
                # Quota problem
                # -------------------------------------------------
                if is_429:

                    return {
                        "answer": (
                            "Gemini API quota has been exhausted. "
                            "Please try again later."
                        ),
                        "model": model_name,
                        "sources": sources,
                        "success": False,
                        "error": (
                            f"Gemini API quota error: "
                            f"{error_text}"
                        ),
                    }

                # -------------------------------------------------
                # Model unavailable
                # -------------------------------------------------
                if "404" in error_text:

                    return {
                        "answer": (
                            "The configured Gemini model is "
                            "currently unavailable for this "
                            "API project."
                        ),
                        "model": model_name,
                        "sources": sources,
                        "success": False,
                        "error": (
                            f"Gemini model error: "
                            f"{error_text}"
                        ),
                    }

                # -------------------------------------------------
                # Other Gemini error
                # -------------------------------------------------
                return {
                    "answer": (
                        "Failed to generate an answer from "
                        "the Gemini API."
                    ),
                    "model": model_name,
                    "sources": sources,
                    "success": False,
                    "error": (
                        f"Gemini API Error: "
                        f"{error_text}"
                    ),
                }

    # ---------------------------------------------------------
    # 7. SDK/import error
    # ---------------------------------------------------------
    except Exception as e:

        error_msg = f"Gemini SDK Error: {str(e)}"

        return {
            "answer": (
                "Failed to initialize the Gemini API client."
            ),
            "model": "error",
            "sources": sources,
            "success": False,
            "error": error_msg,
        }