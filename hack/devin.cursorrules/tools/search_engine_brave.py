#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from typing import Any, List, Optional

from langchain_community.document_loaders import BraveSearchLoader
from langchain_core.documents import Document
from tenacity import retry, stop_after_attempt, wait_exponential


class BraveSearchError(Exception):
    """Custom exception for Brave Search API errors."""
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def search_with_retry(
    query: str,
    api_key: str,
    max_results: int = 10,
) -> list[Document]:
    """
    Search using Brave Search API through LangChain and return results.

    Args:
        query: Search query
        api_key: Brave Search API key
        max_results: Maximum number of results to return

    Returns:
        List of Document objects containing search results

    Raises:
        BraveSearchError: If the search fails after all retries
    """
    try:
        print(f"DEBUG: Searching for query: {query}", file=sys.stderr)

        loader = BraveSearchLoader(
            api_key=api_key,
            search_kwargs={
                "max_results": max_results
            }
        )

        documents = loader.load(query)
        print(f"DEBUG: Found {len(documents)} results", file=sys.stderr)
        return documents

    except Exception as e:
        print(f"ERROR: Search failed: {str(e)}", file=sys.stderr)
        raise BraveSearchError(f"Search failed: {str(e)}") from e

def format_results(documents: Sequence[Document]) -> None:
    """
    Format and print search results from Document objects.

    Args:
        documents: List of Document objects from BraveSearchLoader
    """
    for i, doc in enumerate(documents, 1):
        print(f"\n=== Result {i} ===")
        # Extract URL and title from metadata
        print(f"URL: {doc.metadata.get('source', 'N/A')}")
        print(f"Title: {doc.metadata.get('title', 'N/A')}")
        print(f"Snippet: {doc.page_content}")

def search(
    query: str,
    api_key: str | None = None,
    max_results: int = 10,
) -> None:
    """
    Main search function that handles search with retry mechanism using LangChain.

    Args:
        query: Search query
        api_key: Brave Search API key (can also be set via BRAVE_SEARCH_API_KEY env var)
        max_results: Maximum number of results to return

    Raises:
        BraveSearchError: If the search fails or API key is missing
    """
    # Get API key from argument or environment variable
    api_key = api_key or os.environ.get("BRAVE_SEARCH_API_KEY")
    if not api_key:
        raise BraveSearchError(
            "Brave Search API key is required. Set it via BRAVE_SEARCH_API_KEY "
            "environment variable or --api-key argument"
        )

    try:
        documents = search_with_retry(query, api_key, max_results)
        if documents:
            format_results(documents)
        else:
            print("No results found.", file=sys.stderr)

    except Exception as e:
        print(f"ERROR: Search failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Search using Brave Search API via LangChain")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--api-key", help="Brave Search API key (or set BRAVE_SEARCH_API_KEY env var)")
    parser.add_argument("--max-results", type=int, default=10,
                      help="Maximum number of results (default: 10)")

    args = parser.parse_args()
    search(args.query, args.api_key, args.max_results)

if __name__ == "__main__":
    main()
