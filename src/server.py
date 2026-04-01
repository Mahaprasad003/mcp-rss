#!/usr/bin/env python3
import os

import feedparser
import uvicorn
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

mcp = FastMCP("Poke MCP Server")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy"})


RSS_FEED_URL = "https://mahaprasad.xyz/rss"


@mcp.tool(
    description="Fetch the latest posts from the mahaprasad.xyz RSS feed (DPC Recommends – daily curated DS/ML/DL/NLP resources). Returns raw entries as structured data."
)
def fetch_rss_feed() -> list[dict]:
    """
    Fetches and parses the RSS feed at https://mahaprasad.xyz/rss.
    Returns a list of entries, each with title, link, summary, published date, and tags.
    """
    feed = feedparser.parse(RSS_FEED_URL)

    if feed.bozo and not feed.entries:
        raise RuntimeError(f"Failed to parse RSS feed: {feed.bozo_exception}")

    entries = []
    for entry in feed.entries:
        tags = [tag.term for tag in entry.get("tags", [])] if entry.get("tags") else []
        entries.append(
            {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", ""),
                "published": entry.get("published", ""),
                "author": entry.get("author", ""),
                "tags": tags,
            }
        )

    return entries


@mcp.tool(
    description="Fetch the mahaprasad.xyz RSS feed and return it as formatted text, ready to be summarised."
)
def summarise_rss_feed() -> str:
    """
    Fetches the RSS feed at https://mahaprasad.xyz/rss and returns a formatted,
    human-readable string of all entries for the agent to summarise.
    """
    feed = feedparser.parse(RSS_FEED_URL)

    if feed.bozo and not feed.entries:
        raise RuntimeError(f"Failed to parse RSS feed: {feed.bozo_exception}")

    feed_title = feed.feed.get("title", "RSS Feed")

    entry_lines = []
    for i, entry in enumerate(feed.entries, start=1):
        tags = (
            ", ".join(tag.term for tag in entry.get("tags", []))
            if entry.get("tags")
            else "—"
        )
        entry_lines.append(
            f"{i}. {entry.get('title', 'Untitled')}\n"
            f"   Link:      {entry.get('link', '')}\n"
            f"   Author:    {entry.get('author', '—')}\n"
            f"   Published: {entry.get('published', '—')}\n"
            f"   Tags:      {tags}\n"
            f"   Summary:   {entry.get('summary', '—')}\n"
        )

    return f"# {feed_title}\n\n" + "\n".join(entry_lines)


# CORS middleware required for browser-based clients (e.g. MCP Inspector).
# The MCP protocol needs mcp-protocol-version and mcp-session-id headers,
# and mcp-session-id must be in expose_headers so JS can read it.
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=[
            "mcp-protocol-version",
            "mcp-session-id",
            "Authorization",
            "Content-Type",
        ],
        expose_headers=["mcp-session-id"],
    )
]

app = mcp.http_app(stateless_http=True, middleware=middleware)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    print(f"Starting Poke MCP server on 0.0.0.0:{port}")

    uvicorn.run(app, host="0.0.0.0", port=port)
