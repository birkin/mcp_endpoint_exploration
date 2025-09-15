## imports httpx and mcp framework
import logging
import os
from typing import Annotated, Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

## setup logging
log_level_name: str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(
    logging, log_level_name, logging.INFO
)  # maps the string name to the corresponding logging level constant; defaults to INFO
logging.basicConfig(
    level=log_level,
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S',
    filename='../mcp_endpoint_exploration.log',
)
log = logging.getLogger(__name__)
## prevent httpx from logging
if log_level <= logging.INFO:
    for noisy in ('httpx', 'httpcore'):
        lg = logging.getLogger(noisy)
        lg.setLevel(logging.WARNING)  # or logging.ERROR if you prefer only errors
        lg.propagate = False  # don't bubble up to root


# Initialize our MCP server
mcp = FastMCP("bdr", stateless_http=False)

API_BASE = "https://repository.library.brown.edu/api"
log.debug(f'API_BASE: ``{API_BASE}``')

async def fetch_json(url: str) -> dict[str, Any]:
    """Helper to fetch JSON and raise exceptions on HTTP errors."""
    log.debug('starting fetch_json()')
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=30.0)
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def search_bdr(query: Annotated[str, "Solr syntax query (e.g., primary_title:irish)"],
                     rows: Annotated[Optional[int], "Number of results to return (default 10)"] = 10,
                     fields: Annotated[Optional[str], "Comma‑separated fields to return (e.g., pid,primary_title,abstract)"] = None) -> str:
    """
    Search the Brown Digital Repository using Solr query syntax.

    Args:
      query: A Solr query string (use field names like primary_title or rel_is_member_of_collection_ssim)
      rows: Number of rows to return (default 10)
      fields: Comma‑separated list of fields to include in the response (optional)

    Returns:
      A formatted string summarizing the search results.
    """
    log.debug('starting search_bdr()')
    # Build the search URL
    params = {
        'q': query,
        'rows': rows,
    }
    if fields:
        params['fl'] = fields
    # Compose the query string safely
    url = f"{API_BASE}/search/" + "?" + httpx.QueryParams(params).render()
    log.debug(f'fetching search-url, ``{url}``')
    data = await fetch_json(url)
    docs = data.get('response', {}).get('docs', [])  # The BDR wraps Solr responses in response/docs
    if not docs:
        return "No results found."
    # Format results for LLM consumption
    lines = []
    for doc in docs:
        pid = doc.get('pid') or doc.get('id')
        title = doc.get('primary_title') or doc.get('title_display')
        abstract = doc.get('abstract', '')
        lines.append(f"PID: {pid}\nTitle: {title}\nAbstract: {abstract}\n---")
    return "\n".join(lines)

@mcp.tool()
async def get_bdr_item(pid: Annotated[str, "Persistent identifier of a BDR object (e.g., bdr:80246)"] ) -> str:
    """
    Retrieve detailed metadata about a BDR item.

    Args:
      pid: The item’s persistent identifier (e.g. bdr:80246)

    Returns:
      A summary of the item’s metadata (title, description, relations and collection).
    """
    log.debug('starting get_bdr_item()')
    url = f"{API_BASE}/items/{pid}/"
    log.debug(f'fetching item-url, ``{url}``')
    data = await fetch_json(url)
    title = data.get('primary_title', '(no title)')
    description = data.get('abstract') or data.get('description') or ''
    # Extract collection names
    collections = []
    relations = data.get('relations', {})
    # for c in relations.get('isMemberOfCollection', relations.get('isMemberOfCollection', [])):
    for c in relations.get('isMemberOfCollection', []):
        collections.append(c.get('name'))
    coll_str = ", ".join(collections) if collections else "none"
    return f"Title: {title}\nCollections: {coll_str}\nDescription: {description}"

if __name__ == '__main__':
    # Run via stdio transport for easiest integration with ollmcp or mcphost
    mcp.run(transport='stdio')
