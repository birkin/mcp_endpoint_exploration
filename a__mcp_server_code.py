## imports httpx and mcp framework
import logging
import os
import time
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
log.info(f'API_BASE: ``{API_BASE}``')

async def fetch_json(url: str) -> dict[str, Any]:
    """Helper to fetch JSON and raise exceptions on HTTP errors."""
    log.info('starting fetch_json()')
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=30.0)
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def search_bdr(
    query: Annotated[str, 'Solr query. Prefer fielded terms (e.g., primary_title:"pencil sketch"). Quote phrases; use AND/OR; avoid leading wildcards.'],
    rows: Annotated[int, 'Max docs to return. Use small values (e.g., 5–25) and iterate if needed. Default 10.'] = 10,
    fields: Annotated[Optional[str], 'Optional comma-separated fields to return; pid is always included. Recommend: pid,primary_title,abstract,ir_collection_name,score'] = None,
    sort: Annotated[Optional[str], 'Optional Solr sort, e.g., "score desc" or "date_modified desc"'] = None
) -> dict[str, Any]:
    """
    Search the Brown Digital Repository (BDR) via its Solr-backed Search API.

    ## purpose
    Return a **compact, machine-usable** summary so a model can chain follow-ups
    (e.g., “tell me more about that pencil-sketch”) **without losing PIDs**.

    ## query tips (for the model and for humans)
    - Prefer fielded queries: `primary_title:"pencil sketch"`, `rel_is_member_of_collection_ssim:"bdr:12345"`.
    - Quote multi-word phrases; use `AND`/`OR` explicitly.
    - Avoid leading wildcards (`*term`) for performance; suffix wildcards (`term*`) are OK in moderation.
    - If `response.numFound` is large, reduce scope (add fields/filters) or page with a larger `rows` only when truly needed.

    ## returned structure
    {
      "query": "<original query>",
      "request_url": "<fully-resolved API URL>",
      "num_found": <int>,          # response.numFound (total hits)
      "returned": <int>,           # len(docs) actually returned
      "docs": [
        {
          "pid": "bdr:…",          # _always_ present to support follow-ups
          "title": "…",            # includes PID suffix e.g., "Napoleon at Waterloo -- [bdr:123456]"
          "abstract": "…",
          "ir_collection_name": "…",
          "_score": <float|None>   # if Solr provides it
        },
        ...
      ],
      "warnings": [ "...optional guidance..." ],
      "took_ms": <float>
    }

    ## model usage notes (very important)
    - _Always_ include the item's pid (e.g., "bdr:123456") in any response which references an item.

    ## examples
    - query: primary_title:"irish"
    - query: rel_is_member_of_collection_ssim:"bdr:123456"
    - query: (primary_title:sketch OR abstract:sketch) AND ir_collection_name:"Brown Daily Herald"
    """
    t0 = time.perf_counter()

    # default fields we *always* want for follow-ups; merge with user-supplied
    default_fl = {'pid', 'primary_title', 'abstract', 'ir_collection_name', 'score'}
    user_fl = set()
    if fields:
        user_fl = {f.strip() for f in fields.split(',') if f.strip()}
    fl = ','.join(sorted(default_fl | user_fl))

    params: dict[str, Any] = {'q': query, 'rows': rows, 'fl': fl}
    if sort:
        params['sort'] = sort

    url = f'{API_BASE}/search/?' + str(httpx.QueryParams(params))
    data = await fetch_json(url)

    resp = data.get('response', {}) or {}
    num_found = int(resp.get('numFound') or 0)
    raw_docs = resp.get('docs', []) or []

    # normalize docs into a lean shape (keep PIDs!)
    docs = []
    for d in raw_docs:
        pid = d.get('pid') or d.get('id')
        base_title = d.get('primary_title') or d.get('title_display')
        # Build title with PID suffix per requirement
        if base_title:
            title = f"{base_title} -- [{pid}]" if pid else base_title
        else:
            title = f"[{pid}]" if pid else "(no title)"
        docs.append({
            'pid': pid,
            'title': title,
            'abstract': d.get('abstract'),
            'ir_collection_name': d.get('ir_collection_name'),
            '_score': d.get('score'),
        })

    warnings: list[str] = []
    if num_found > rows:
        warnings.append(
            f'Query returned {num_found} hits but only {rows} were fetched. '
            'Refine the query (add fields/filters) or increase `rows` only if necessary.'
        )
    if not docs:
        warnings.append('No results. Consider relaxing filters or trying a broader fielded query.')

    took_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return {
        'query': query,
        'request_url': url,
        'num_found': num_found,
        'returned': len(docs),
        'docs': docs,
        'warnings': warnings,
        'took_ms': took_ms,
    }

# async def search_bdr(query: Annotated[str, "Solr syntax query (e.g., irish"],
#                      rows: Annotated[Optional[int], "Number of results to return (default 10)"] = 10,
#                      fields: Annotated[Optional[str], "Comma‑separated fields to return (e.g., pid,primary_title,abstract)"] = None) -> str:
#     """
#     Search the Brown Digital Repository using Solr query syntax.

#     Args:
#       query: A Solr query string
#         - for broadest results, just use the required term.
#         - optional: use field names like primary_title or rel_is_member_of_collection_ssim
#       rows: Number of rows to return (default 10)
#       fields: Comma‑separated list of fields to include in the response (optional)

#     Returns:
#       json results. 
#       Useful fields include:
#       - "response"-->"numFound" -- showing the total number of results, even if only a few were returned.
#       - in "response"-->"docs", each item contains an "ir_collection_name" showing the collection the item is a part of.
#     """
#     log.info('starting search_bdr()')
#     # Build the search URL
#     params = {
#         'q': query,
#         'rows': rows,
#     }
#     if fields:
#         params['fl'] = fields
#     # Compose the query string safely
#     url = f"{API_BASE}/search/" + "?" + str(httpx.QueryParams(params))
#     log.info(f'fetching search-url, ``{url}``')
#     data = await fetch_json(url)
#     docs = data.get('response', {}).get('docs', [])  # The BDR wraps Solr responses in response/docs
#     if not docs:
#         return "No results found."
#     # Format results for LLM consumption
#     lines = []
#     for doc in docs:
#         pid = doc.get('pid') or doc.get('id')
#         title = doc.get('primary_title') or doc.get('title_display')
#         abstract = doc.get('abstract', '')
#         lines.append(f"PID: {pid}\nTitle: {title}\nAbstract: {abstract}\n---")
#     return "\n".join(lines)

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
