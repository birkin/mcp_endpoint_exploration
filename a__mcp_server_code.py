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
log.info(f'API_BASE: ``{API_BASE}``')

async def fetch_json(url: str) -> dict[str, Any]:
    """Helper to fetch JSON and raise exceptions on HTTP errors."""
    log.info('starting fetch_json()')
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=30.0)
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def search_bdr(query: Annotated[str, "Solr syntax query (e.g., irish"],
                     rows: Annotated[Optional[int], "Number of results to return (default 10)"] = 10,
                     fields: Annotated[Optional[str], "Comma‑separated fields to return (e.g., pid,primary_title,abstract)"] = None) -> str:
    """
    Search the Brown Digital Repository using Solr query syntax.

    Args:
      query: A Solr query string
        - for broadest results, just use the required term.
        - optional: use field names like primary_title or rel_is_member_of_collection_ssim
      rows: Number of rows to return (default 10)
      fields: Comma‑separated list of fields to include in the response (optional)

    Returns:
      JSON summarizing the results. 
      Useful fields include 
      - "response"-->"numFound" -- showing the total number of results, even if only a few were returned.
      - in "response"-->"docs", each item contains an "ir_collection_name" showing the collection the item is a part of.

    Other useful info:
(useful-info-start)
    ```
    ## Info

The BDR Search API is based on [Solr], one of the two most popular indexers in the world, so many developers will be familiar with it, and there are many online resources for how to structure queries (one [example-resource]). It doesn't support all of Solr's query features, but does support many useful ones. In general, the search query should be formatted the same way as standard Solr queries.

If the query is badly formatted, a ‘400 / Bad Request’ response will be returned.

If the search is successful (even if there are no results), a ‘200 / OK’ response will be returned.

[Solr]: <https://en.wikipedia.org/wiki/Apache_Solr>
[example-resource]: <https://lucene.apache.org/solr/guide/8_1/common-query-parameters.html#common-query-parameters>


## Structure

`https://repository.library.brown.edu/api/search/?[ search-query ]`
* Example: <https://repository.library.brown.edu/api/search/?q=primary_title:irish&rows=25>
*Note that although over 100 results are found, only 25 are returned*


## Examples

- Query on title with row-definition
	- url: <https://repository.library.brown.edu/api/search/?q=primary_title:irish&rows=25>
	- note that although over 100 results are found, only 25 are returned
	- note that each result shows some 50+ elements of each result. Let's say you really only wanted a link to the item-id,title, and description. You could get those filtered results via: <https://repository.library.brown.edu/api/search/?q=primary_title:irish&rows=25&fl=pid,primary_title,abstract>
		- added `&fl=pid,primary_title,abstract`
	- and to get to the next 25: <https://repository.library.brown.edu/api/search/?q=primary_title:irish&rows=25&fl=pid,primary_title,abstract&start=25>
		- added `&start=25` (0 through 24 were the first 25)

- Find items in a collection, only returning title and pid
	- url: <https://repository.library.brown.edu/api/search/?q=rel_is_member_of_collection_ssim:%22bdr:wum3gm43%22&fl=primary_title,pid>
	- sometimes can provide more flexibility to specify the data returned than using the collections-api.

- Find items in a collection where the title does _NOT_ contain the word 'Page'
	- url: <https://repository.library.brown.edu/api/search/?q=rel_is_member_of_collection_ssim:%22bdr:wum3gm43%22%20AND%20-primary_title:*Page*&fl=primary_title,pid>
	- specifies that only the `primary_title` and `pid` fields are returned.

- Find items in a collection for those items that are _NOT_ part of another collection
	- url: <https://repository.library.brown.edu/api/search/?q=rel_is_member_of_collection_ssim:%22bdr:wum3gm43%22+-rel_is_part_of_ssim:*&fl=primary_title,pid>

- Real world example where I wanted to find hall-hoag org-items that didn't have a particular data-element
    - url-human: ```https://repository.library.brown.edu/api/search/?q=rel_is_member_of_collection_ssim:"bdr:wum3gm43" AND 
-mods_record_info_note_hallhoagorglevelrecord_ssim:"Organization Record" AND -rel_is_part_of_ssim:*```
    - url encoded and usable: <https://repository.library.brown.edu/api/search/?q=rel_is_member_of_collection_ssim:%22bdr:wum3gm43%22%20AND%20%20-mods_record_info_note_hallhoagorglevelrecord_ssim:%22Organization%20Record%22%20AND%20-rel_is_part_of_ssim:*>
    - explanation:
        - is member of hall-hoag collection
        - does not have a particular record-info-note data-element
        - is not part-of another object
    - note: once I add the data-element, the url will return zero items -- this is just a documentation example of how the apis can be useful to find records in need of data-cleanup.
(useful-info-END)
    ```

    Returns:
      A formatted string summarizing the search results.
    """
    log.info('starting search_bdr()')
    # Build the search URL
    params = {
        'q': query,
        'rows': rows,
    }
    if fields:
        params['fl'] = fields
    # Compose the query string safely
    url = f"{API_BASE}/search/" + "?" + str(httpx.QueryParams(params))
    log.info(f'fetching search-url, ``{url}``')
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
